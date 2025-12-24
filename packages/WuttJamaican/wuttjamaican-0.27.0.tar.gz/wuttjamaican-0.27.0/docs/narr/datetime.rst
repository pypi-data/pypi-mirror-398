
===================
 DateTime Behavior
===================

There must be a way to handle :class:`~python:datetime.datetime` data,
such that we can keep straight any timezone(s) which may be involved
for the app.

As a rule, we store datetime values as "naive/UTC" within the
:term:`app database`, and convert to "aware/local" as needed for
display to the user etc.

A related rule is that any *naive* datetime is assumed to be UTC.  If
you have a naive/local value then you should convert it to aware/local
or else the framework logic will misinterpret it.  (See below,
:ref:`convert-to-localtime`.)

With these rules in place, the workhorse methods are:

* :meth:`~wuttjamaican.app.AppHandler.localtime()`
* :meth:`~wuttjamaican.app.AppHandler.make_utc()`
* :meth:`~wuttjamaican.app.AppHandler.render_datetime()`


Time Zone Config/Lookup
-----------------------

Technically no config is required; the default timezone can be gleaned
from the OS::

   # should always return *something* :)
   tz_default = app.get_timezone()

The default (aka. local) timezone is used by
:meth:`~wuttjamaican.app.AppHandler.localtime()` and therefore also
:meth:`~wuttjamaican.app.AppHandler.render_datetime()`.

Config can override the default/local timezone; it's assumed most apps
will do this.  If desired, other alternate timezone(s) may be
configured as well:

.. code-block:: ini

   [wutta]
   timezone.default = America/Chicago
   timezone.eastcoast = America/New_York
   timezone.westcoast = America/Los_Angeles

Corresponding :class:`python:datetime.tzinfo` objects can be fetched
via :meth:`~wuttjamaican.app.AppHandler.get_timezone()`::

   tz_default = app.get_timezone() # => America/Chicago

   tz_eastcoast = app.get_timezone("eastcoast")
   tz_westcoast = app.get_timezone("westcoast")


UTC vs. Local Time
------------------

Since we store values as naive/UTC, but display to the user as
aware/local, we often need to convert values between these (and
related) formats.


.. _convert-to-utc:

Convert to UTC
~~~~~~~~~~~~~~

When a datetime value is written to the app DB, it must be naive/UTC.

Below are 4 examples for converting values to UTC time zone.  In
short, use :meth:`~wuttjamaican.app.AppHandler.make_utc()` - but if
providing a naive value, it must already be UTC!  (Because *all* naive
values are assumed to be UTC.  Provide zone-aware values when
necessary to avoid confusion.)

These examples assume ``America/Chicago`` (UTC-0600) for the "local"
timezone, with a local time value of 2:15 PM (so, 8:15 PM UTC)::

   # naive/UTC => naive/UTC
   # (nb. this conversion is not actually needed of course, but we
   # show the example to be thorough)
   # nb. value has no timezone but is already correct (8:15 PM UTC)
   dt = datetime.datetime(2025, 12, 16, 20, 15)
   utc = app.make_utc(dt)

   # aware/UTC => naive/UTC
   # nb. value has expicit timezone, w/ correct time (8:15 PM UTC)
   dt = datetime.datetime(2025, 12, 16, 20, 15, tzinfo=datetime.timezone.utc)
   utc = app.make_utc(dt)

   # aware/local => naive/UTC
   tzlocal = app.get_timezone()
   # nb. value has expicit timezone, w/ correct time (2:15 PM local)
   dt = datetime.datetime(2025, 12, 16, 14, 15, tzinfo=tzlocal)
   utc = app.make_utc(dt)

If your value is naive/local then you can't simply pass it to
:meth:`~wuttjamaican.app.AppHandler.make_utc()` - since that assumes
naive values are already UTC.  (Again, *all* naive values are assumed
to be UTC.)

Instead, first call :meth:`~wuttjamaican.app.AppHandler.localtime()`
with ``from_utc=False`` to add local time zone awareness::

   # naive/local => naive/UTC
   # nb. value has no timezone but is correct for local zone (2:15 PM)
   dt = datetime.datetime(2025, 12, 16, 14, 15)
   # must first convert, and be sure to specify it's *not* UTC
   # (in practice this just sets the local timezone)
   dt = app.localtime(dt, from_utc=False)
   # value is now "aware/local" so can proceed
   utc = app.make_utc(dt)

The result of all examples shown above (8:15 PM UTC)::

   >>> utc
   datetime.datetime(2025, 12, 16, 20, 15)


.. _convert-to-localtime:

Convert to Local Time
~~~~~~~~~~~~~~~~~~~~~

When a datetime value is read from the app DB, it must be converted
(from naive/UTC) to aware/local for display to user.

Below are 4 examples for converting values to local time zone.  In
short, use :meth:`~wuttjamaican.app.AppHandler.localtime()` - but if
providing a naive value, you should specify ``from_utc`` param as
needed.

These examples assume ``America/Chicago`` (UTC-0600) for the "local"
timezone, with a local time value of 2:15 PM (so, 8:15 PM UTC)::

   # naive/UTC => aware/local
   # nb. value has no timezone but is already correct (8:15 PM UTC)
   dt = datetime.datetime(2025, 12, 16, 20, 15)
   # nb. can omit from_utc since it is assumed for naive values
   local = app.localtime(dt)
   # nb. or, specify it explicitly anyway
   local = app.localtime(dt, from_utc=True)

   # aware/UTC => aware/local
   # nb. value has expicit timezone, w/ correct time (8:15 PM UTC)
   dt = datetime.datetime(2025, 12, 16, 20, 15, tzinfo=datetime.timezone.utc)
   local = app.localtime(dt)

   # aware/local => aware/local
   # (nb. this conversion is not actually needed of course, but we
   # show the example to be thorough)
   tzlocal = app.get_timezone()
   # nb. value has expicit timezone, w/ correct time (2:15 PM local)
   dt = datetime.datetime(2025, 12, 16, 14, 15, tzinfo=tzlocal)
   # nb. the input and output values are the same here, both aware/local
   local = app.localtime(dt)

If your value is naive/local then you can't simply pass it to
:meth:`~wuttjamaican.app.AppHandler.localtime()` with no qualifiers -
since that assumes naive values are already UTC by default.

Instead specify ``from_utc=False`` to ensure the value is interpreted
correctly::

   # naive/local => aware/local
   # nb. value has no timezone but is correct for local zone (2:15 PM)
   dt = datetime.datetime(2025, 12, 16, 14, 15)
   # nb. must specify from_utc to avoid misinterpretation
   local = app.localtime(dt, from_utc=False)

The result of all examples shown above (2:15 PM local)::

   >>> local
   datetime.datetime(2025, 12, 16, 14, 15, tzinfo=zoneinfo.ZoneInfo("America/Chicago"))


Displaying to the User
----------------------

Whenever a datetime should be displayed to the user, call
:meth:`~wuttjamaican.app.AppHandler.render_datetime()`.  That will (by
default) convert the value to aware/local and then render it using a
common format.

(Once again, this will *not* work for naive/local values.  Those must
be explicitly converted to aware/local since the framework assumes
*all* naive values are in UTC.)

You can specify ``local=False`` when calling ``render_datetime()`` to
avoid its default conversion.

See also :ref:`convert-to-localtime` (above) for examples of how to
convert any value to aware/local.

.. code-block:: python

   # naive/UTC
   dt = app.make_utc()
   print(app.render_datetime(dt))

   # aware/UTC
   dt = app.make_utc(tzinfo=True)
   print(app.render_datetime(dt))

   # aware/local
   dt = app.localtime()
   print(app.render_datetime(dt))

   # naive/local
   dt = datetime.datetime.now()
   # nb. must explicitly convert to aware/local
   dt = app.localtime(dt, from_utc=False)
   # nb. can skip redundant conversion via local=False
   print(app.render_datetime(dt, local=False))


Within the Database
-------------------

This section describes storage and access details for datetime values
within the :term:`app database`.


Column Type
~~~~~~~~~~~

There is not a consistent/simple way to store timezone for datetime
values in all database backends.  Therefore we must always store the
values as naive/UTC so app logic can reliably interpret them.  (Hence
that particular rule.)

All built-in :term:`data models <data model>` use the
:class:`~sqlalchemy:sqlalchemy.types.DateTime` column type (for
datetime fields), with its default behavior.  Any app schema
extensions should (usually) do the same.


Writing to the DB
~~~~~~~~~~~~~~~~~

When a datetime value is written to the app DB, it must be naive/UTC.

See :ref:`convert-to-utc` (above) for examples of how to convert any
value to naive/UTC.

Apps typically "write" data via the ORM.  Regardless, the key point is
that you should only pass naive/UTC values into the DB::

   model = app.model
   session = app.make_session()

   # obtain aware/local value (for example)
   tz = app.get_timezone()
   dt = datetime.datetime(2025, 12, 16, 14, 15, tzinfo=tz)

   # convert to naive/UTC when passing to DB
   sprocket = model.Sprocket()
   sprocket.some_dt_attr = app.make_utc(dt)
   sprocket.created = app.make_utc() # "now"
   session.add(sprocket)

   session.commit()


Reading from the DB
~~~~~~~~~~~~~~~~~~~

Nothing special happens when reading datetime values from the DB; they
will be naive/UTC just like they were written::

   sprocket = session.get(model.Sprocket, uuid)

   # these will be naive/UTC
   dt = sprocket.some_dt_attr
   dt2 = sprocket.created
