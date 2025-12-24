
Conventions
===========

Below are recommended conventions for structuring and naming the files
in your project relating to import/export.

The intention for these rules is that they are "intuitive" based on
the fact that all data flows from source to target and therefore can
be thought of as "importing" in virtually all cases.

But there are a lot of edge cases out there so YMMV.


"The Rules"
-----------

There are exceptions to these of course, but in general:

* regarding how to think about these conventions:

  * always look at it from target's perspective

  * always look at it as an *import*, not export

* "final" logic is always a combo of:

  * "base" logic for how target data read/write happens generally

  * "specific" logic for how that happens using a particular data source

* targets each get their own subpackage within project

  * and within that, also an ``importing`` (nested) subpackage

    * and within *that* is where the files live, referenced next

  * target ``model.py`` should contain ``ToTarget`` importer base class

    * also may have misc. per-model base classes, e.g. ``WidgetImporter``

    * also may have ``ToTargetHandler`` base class if applicable

  * sources each get their own module, named after the source

    * should contain the "final" handler class, e.g. ``FromSourceToTarget``

    * also contains "final" importer classes needed by handler (e.g. ``WidgetImporter``)


Example
-------

That's a lot of rules so let's see it.  Here we assume a Wutta-based
app named Poser and it integrates with a Foo API in the cloud.  Data
should flow both ways so we will be thinking of this as:

* **Foo → Poser import**
* **Poser → Foo export**

Here is the suggested file layout:

.. code-block:: none

   poser/
   ├── foo/
   │   ├── __init__.py
   │   ├── api.py
   │   └── importing/
   │       ├── __init__.py
   │       ├── model.py
   │       └── poser.py
   └── importing/
       ├── __init__.py
       ├── foo.py
       └── model.py

And the module breakdown:

* ``poser.foo.api`` has e.g. ``FooAPI`` interface logic

**Foo → Poser import** (aka. "Poser imports from Foo")

* ``poser.importing.model`` has ``ToPoserHandler``, ``ToPoser`` and per-model base importers
* ``poser.importing.foo`` has ``FromFooToPoser`` plus final importers

**Poser → Foo export** (aka. "Foo imports from Poser")

* ``poser.foo.importing.model`` has ``ToFooHandler``, ``ToFoo`` and per-model base importer
* ``poser.foo.importing.poser`` has ``FromPoserToFoo`` plus final importers
