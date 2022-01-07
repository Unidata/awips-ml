#!/bin/sh
set -e
/usr/bin/edex start
/usr/bin/rm -rf /awips2/edex/data/hdf5/satellite
/awips2/psql/bin/psql -U awips -c "delete from satellite;" metadata
/awips2/psql/bin/psql -U awips -c "delete from satellite_spatial;" metadata
