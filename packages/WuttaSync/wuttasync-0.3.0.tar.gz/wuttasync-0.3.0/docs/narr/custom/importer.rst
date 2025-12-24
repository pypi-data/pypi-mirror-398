
Define Importer(s)
==================

Here we'll describe how to make a custom :term:`importer/exporter
<importer>`, which can process a given :term:`data model`.

..
   The example will assume a **Foo → Poser import** for the ``Widget``
   :term:`data model`.


Choose the Base Class(es)
-------------------------

As with the :term:`import handler`, the importer "usually" will have
two base classes: one for the target side and another for the source.

The base class for target side is generally more fleshed out, with
logic to read/write data for the given target model.  Whereas the base
class for the source side could just be a stub.  In the latter case,
one might choose to skip it and inherit only from the target base
class.

In any case the final importer class you define can override any/all
logic from either base class if needed.


Example: Foo → Poser import
---------------------------

Here we'll assume a Wutta-based app named "Poser" which will be
importing "Widget" data from the "Foo API" cloud service.

In this case we will inherit from a base class for the target side,
which already knows how to talk to the :term:`app database` via
SQLAlchemy ORM.

But for the source side, there is no existing base class for the Foo
API service, since that is just made-up - so we will also define our
own base class for that::

   from wuttasync.importing import Importer, ToWutta

   # nb. this is not real of course, but an example
   from poser.foo.api import FooAPI

   class FromFoo(Importer):
      """
      Base class for importers using Foo API as source
      """

      def setup(self):
          """
          Establish connection to Foo API
          """
          self.foo_api = FooAPI(self.config)

   class WidgetImporter(FromFoo, ToWutta):
      """
      Widget importer for Foo -> Poser
      """

      def get_source_objects(self):
          """
          Fetch all "raw" widgets from Foo API
          """
          # nb. also not real, just example
          return self.foo_api.get_widgets()

      def normalize_source_object(self, widget):
          """
          Convert the "raw" widget we receive from Foo API, to a
          "normalized" dict with data for all fields which are part of
          the processing request.
          """
          return {
              'id': widget.id,
              'name': widget.name,
          }


Example: Poser → Foo export
---------------------------

In the previous scenario we imported data from Foo to Poser, and here
we'll do the reverse, exporting from Poser to Foo.

As of writing the base class logic for exporting from Wutta :term:`app
database` does not yet exist.  And the Foo API is just made-up so
we'll add one-off base classes for both sides::

   from wuttasync.importing import Importer

   class FromWutta(Importer):
      """
      Base class for importers using Wutta DB as source
      """

   class ToFoo(Importer):
      """
      Base class for exporters targeting Foo API
      """

   class WidgetImporter(FromWutta, ToFoo):
      """
      Widget exporter for Poser -> Foo
      """

      def get_source_objects(self):
         """
         Fetch all widgets from the Poser app DB.

         (see note below regarding the db session)
         """
         model = self.app.model
         return self.source_session.query(model.Widget).all()

      def normalize_source_object(self, widget):
          """
          Convert the "raw" widget from Poser app (ORM) to a
          "normalized" dict with data for all fields which are part of
          the processing request.
          """
          return {
              'id': widget.id,
              'name': widget.name,
          }

Note that the ``get_source_objects()`` method shown above makes use of
a ``source_session`` attribute - where did that come from?

This is actually not part of the importer proper, but rather this
attribute is set by the :term:`import handler`.  And that will ony
happen if the importer is being invoked by a handler which supports
it.  So none of that is shown here, but FYI.

(And again, that logic isn't written yet, but there will "soon" be a
``FromSqlalchemyHandler`` class defined which implements this.)


Regster with Import Handler
---------------------------

After you define the importer/exporter class (as shown above) you also
must "register" it within the import/export handler.

This section is here for completeness but the process is described
elsewhere; see :ref:`register-importer`.
