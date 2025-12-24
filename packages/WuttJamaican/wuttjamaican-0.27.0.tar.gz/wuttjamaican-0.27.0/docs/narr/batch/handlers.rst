
Batch Handlers
==============

The :term:`batch handler` is responsible for all logic surrounding a
:term:`batch`: creation, updates, execution.

Each batch handler is associated with one :term:`batch type`.  There
may be more than one handler defined for a given batch type.  However
only one handler will be designated as the "default" for each batch
type (based on config and app defaults).


Class Definition
----------------

A new batch handler class should inherit from
:class:`~wuttjamaican.batch.BatchHandler`, which provides most of the
typical housekeeping logic etc.

Note that it also must declare the
:attr:`~wuttjamaican.batch.BatchHandler.model_class`, which ultimately
determines the handler's :term:`batch type`.

You will need to define/override some methods for the new handler to
be useful::

   from wuttjamaican.batch import BatchHandler
   from poser.db.model import InventoryBatch

   class InventoryBatchHandler(BatchHandler):
       """ Handler for inventory count batches """

       # direct reference to batch model class
       model_class = InventoryBatch

       def execute(self, batch, user=None, progress=None, **kwargs):
           """ export batch row data to CSV """
