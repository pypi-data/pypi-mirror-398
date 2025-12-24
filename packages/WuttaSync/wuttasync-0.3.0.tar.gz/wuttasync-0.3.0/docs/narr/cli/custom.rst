
=================
 Custom Commands
=================

This section describes how to add a custom :term:`subcommand` which
wraps a particular :term:`import handler`.

See also :doc:`wuttjamaican:narr/cli/custom` for more information
on the general concepts etc.


Basic Import/Export
-------------------

Here we'll assume you have a typical "Poser" app based on Wutta
Framework, and the "Foo → Poser" (``FromFooToPoser`` handler) import
logic is defined in the ``poser.importing.foo`` module.

We'll also assume you already have a ``poser`` top-level
:term:`command` (in ``poser.cli``), and our task now is to add the
``poser import-foo`` subcommand to wrap the import handler.

And finally we'll assume this is just a "typical" import handler and
we do not need any custom CLI params exposed.

Here is the code and we'll explain below::

   from poser.cli import poser_typer
   from wuttasync.cli import import_command, ImportCommandHandler

   @poser_typer.command()
   @import_command
   def import_foo(ctx, **kwargs):
       """
       Import data from Foo API to Poser DB
       """
       config = ctx.parent.wutta_config
       handler = ImportCommandHandler(
           config, import_handler='poser.importing.foo:FromFooToPoser')
       handler.run(ctx.params)

Hopefully it's straightforward but to be clear:

* subcommand is really just a function, **with desired name**
* wrap with ``@poser_typer.command()`` to register as subcomand
* wrap with ``@import_command`` to get typical CLI params
* call ``ImportCommandHandler.run()`` with import handler spec

So really - in addition to
:func:`~wuttasync.cli.base.import_command()` - the
:class:`~wuttasync.cli.base.ImportCommandHandler` is doing the heavy
lifting for all import/export subcommands, it just needs to know which
:term:`import handler` to use.

.. note::

   If your new subcommand is defined in a different module than is the
   top-level command (e.g. as in example above) then you may need to
   "eagerly" import the subcommand module.  (Otherwise auto-discovery
   may not find it.)

   This is usually done from within the top-level command's module,
   since it is always imported early due to the entry point.
