
Batch Models
============

Each :term:`batch type` will involve 2 tables in the :term:`app
database`.  Each table is mapped to a :term:`data model` as shown
below.

Note that the model should only describe the data structure; all logic
belongs in the :term:`batch handler`.


Batch (header)
--------------

The model class for the batch header should inherit from
:class:`~wuttjamaican.db.model.batch.BatchMixin`, which gives it the
base set of columns for identifying the batch creator/executor etc.

Declaring the
:attr:`~wuttjamaican.db.model.batch.BatchMixin.batch_type` is
optional; if not specified the table name is used.  Remember the batch
type is used for batch handler lookup (among other things).

Additional columns may be added as needed, per the nature of the batch
type::

   import sqlalchemy as sa
   from wuttjamaican.db import model

   class InventoryBatch(model.BatchMixin, model.Base):
       """ Simple batch for counting inventory. """

       # name of table within the app DB
       __tablename__ = "poser_batch_inventory"

       # unique identifier for this batch type
       batch_type = "inventory"

       device = sa.Column(sa.String(length=255), nullable=True, doc="""
       Name of the scanning device used when counting.
       """)


Batch Row
---------

The model class for batch rows should inherit from
:class:`~wuttjamaican.db.model.batch.BatchRowMixin`, which gives it
the base set of columns for tracking status etc.

Note that it also must declare the
:attr:`~wuttjamaican.db.model.batch.BatchRowMixin.__batch_class__` for
things to work correctly.

Additional columns may be added as needed, per the nature of the batch
type::

   class InventoryBatchRow(model.BatchRowMixin, model.Base):
       """ Item entry row for inventory counting. """

       # name of table within the app DB
       __tablename__ = "poser_batch_inventory_row"

       # direct reference to batch model class
       __batch_class__ = InventoryBatch

       scancode = sa.Column(sa.String(length=14), nullable=False, doc="""
       Scanned UPC of the item.
       """)

       quantity = sa.Column(sa.Numeric(precision=6, scale=2), nullable=False, default=0, doc="""
       Quantity of the item.
       """)
