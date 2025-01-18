import os
from os import listdir
from os.path import isfile, join
from hackathon.utils.settings.settings_provider import SettingsProvider
from hackathon.models import MenuMetadata, menu_metadata_keys
from hackathon.ingestion.menu import MenuIngestor
from hackathon.ingestion.chains import menu_metadata_extractor

from langchain_chroma.vectorstores import Chroma
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

from tqdm import tqdm
import torch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorstoreManager:
    def __init__(self):
        self._embeddings = None
        self._vectorstore = None
        self._retriever = None

        self.settings_provider = SettingsProvider()

    def _setup_vectorstore(self):
        # Setup the vectorstore
        logger.info("Initializing vectorstore...")

        # Setup the torch device
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"

        # Setup the model for embeddings
        model_kwargs = {"device": device}
        encode_kwargs = {"normalize_embeddings": False}

        self._embeddings = HuggingFaceEmbeddings(
            model_name=self.settings_provider.get_embeddings_model_name(),
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )

        self._vectorstore = Chroma(
            persist_directory=self.settings_provider.get_vectorstore_path(),
            embedding_function=self._embeddings,
        )

        # Check if the knowledge base must be loaded
        # to avoid loading it multiple times
        if len(self.vectorstore.get()["documents"]) == 0:  # type: ignore
            self._load_knowledge_base()

        else:
            logger.info("Knowledge base already loaded. Skipping...")

        logger.info("Vectorstore initialized successfully.")

        # Setup the retriever
        self._retriever = self._vectorstore.as_retriever(search_kwargs={"k": 5})

    @property
    def embeddings(self) -> Embeddings:
        if not self._embeddings:
            self._setup_vectorstore()
        return self._embeddings  # type: ignore

    @property
    def vectorstore(self) -> VectorStore:
        if not self._vectorstore:
            self._setup_vectorstore()
        return self._vectorstore  # type: ignore

    @property
    def retriever(self) -> VectorStoreRetriever:
        if not self._retriever:
            self._setup_vectorstore()
        return self._retriever  # type: ignore

    def _load_knowledge_base(self, dir_path: str | None = None):
        """Load knowledge base from a directory into the vectorstore.

        Args:
            directory_path: The path to the directory containing the knowledge base.
                If None, the default knowledge base directory is used.

        """

        # Load the source of truth documents
        # self._load_source_of_truth()

        self._load_menus()

    def is_document_in_vectorstore(self, document: Document) -> bool:
        """Check if a document is already in the vectorstore.

        Args:
            document: The document to check.

        Returns:
            True if the document is in the vectorstore, False otherwise.
        """
        query_results = self.vectorstore.similarity_search(
            document.page_content,
            k=1,
        )
        return query_results == document

    def add_document(self, document: Document):
        """Add a document to the vectorstore.

        Args:
            document: The document to add.
        """
        if self.is_document_in_vectorstore(document):
            return

        self.vectorstore.add_texts(
            texts=[document.page_content],
            metadatas=[document.metadata],
        )

    def add_documents(self, documents: list[Document]):
        """Add a list of documents to the vectorstore.

        Args:
            documents: The list of documents to add.
        """
        for doc in tqdm(documents, desc="Adding documents to vectorstore"):
            self.add_document(doc)

    def _load_source_of_truth(self):
        sources = [
            self.settings_provider.get_galactic_code_path(),
            self.settings_provider.get_cooking_manual_path(),
        ]

        # TO markdown

        # Chunk documents
        # doc_splits ...

        # Add documents to the vectorstore
        # for doc in tqdm(
        #     doc_splits, desc="Adding source of truth documents to vectorstore"
        # ):
        #     metadata = doc.metadata.extends({"source_of_truth": True})
        #     self.vectorstore.add_texts(
        #         texts=[doc.page_content],
        #         metadatas=[metadata],
        #     )

    def _load_menus(self):
        menu_path = self.settings_provider.get_menu_path()

        if not os.path.exists(menu_path):
            raise FileNotFoundError(f"Menu file not found at path: {menu_path}")

        # Load the menu documents
        menu_file_names = [
            file for file in listdir(menu_path) if isfile(join(menu_path, file))
        ]

        # Define the menu ingestor
        menu_ingestor = MenuIngestor()

        # Scan the menu files
        for menu in tqdm(menu_file_names, desc="Adding menu documents to vectorstore"):
            # Load all chunks of the given menu
            menu_splits = menu_ingestor.ingest(os.path.join(menu_path, menu))

            # Take the first chunk as the header
            menu_header = menu_splits[0]

            # call llm to extract metadata
            header_metadata = menu_metadata_extractor.invoke(
                {"document": menu_header, "metadata": menu_metadata_keys}
            )

            # Convert the structured output to dict
            header_metadata = header_metadata.model_dump()
            header_metadata["restaurant_name"] = menu.split(".")[0].lower()

            # Add each document chunk to the vector store
            for chunk in menu_splits:
                # TODO: extract additional metadata from other chunks
                self.vectorstore.add_texts(
                    texts=[chunk.page_content],
                    metadatas=[chunk.metadata.update(header_metadata)],
                )


if __name__ == "__main__":
    vm = VectorstoreManager()
    vm._load_knowledge_base()
