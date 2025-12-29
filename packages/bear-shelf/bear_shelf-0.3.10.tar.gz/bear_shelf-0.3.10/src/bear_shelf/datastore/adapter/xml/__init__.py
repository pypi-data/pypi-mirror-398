"""A set of XML adapters for the datastore module."""

from .deserialize import XMLDeserializer
from .serialize import XMLSerializer

__all__ = ["XMLDeserializer", "XMLSerializer"]
