====================
plonetheme.imioapps
====================

Site theme shared between imio's applications.

Fixed header :
--------------

From version 2.1, the header is fixed (always visible), to remove this, add this to a ploneCustom.css :

.. code:: css

  div#portal-header {
     position: relative;
  }

  #portal-top div#emptyviewlet {
      padding-top: 0em;
  }


Dashboard table sticky header :
-------------------------------

From version 2.22, the tablea header is stikcy (will be sticked to the page header when scrolling down),
to remove this, add this to a ploneCustom.css :

.. code:: css

  table.faceted-table-results th {

    position: inherit;

  }
