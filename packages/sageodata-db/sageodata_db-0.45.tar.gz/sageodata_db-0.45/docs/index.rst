#########################################
sageodata_db Python package documentation
#########################################

Hello! This documentation is about the Python package sageodata_db. This package provides 
code to make it easier to access and use data stored in SA Geodata. 


.. toctree::
   :maxdepth: 5
   :caption: Contents:

   installation
   predefined-queries
   apidocs


.. toctree::
   :caption: Other documentation
   
   Other versions <../index.html#http://>
   Other packages <../../index.html#http://>

*********
Changelog
*********

Version 0.45 (23 December 2025)
===============================
- Move from cx_Oracle to oracledb following upgrade to Oracle version in September in PIRSA to DEW migration

Version 0.23 (24/11/2023)
=========================
- Fix #2 - data_available query's salinities field incorrect - was counting only water chem. 
  Now counting salinity samples as well.

Version 0.14
============
- Add pressure fields to water_levels predefined query (#3)
