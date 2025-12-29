"""
Clarvynn Core - Shared components for all adapters.

This is a namespace package that allows adapters to import from:
  from core.cpl_engine.python.production_cpl_adapter import ProductionCPLAdapter

Installation:
  Set PYTHONPATH to include the repository root:
  export PYTHONPATH="${PYTHONPATH}:$(pwd)"
"""

__path__ = __import__("pkgutil").extend_path(__path__, __name__)
