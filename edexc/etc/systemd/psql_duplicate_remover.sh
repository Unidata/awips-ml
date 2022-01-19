#!/bin/bash

set -e

# this method bluntly just destroys any records (even if they've been ingested) if they are duplicates
delete_duplicates() {
    /awips2/psql/bin/psql -U awips -c "DELETE FROM satellite \
        WHERE satellite.coverage_gid NOT IN ( \
            SELECT DISTINCT ON (the_geom) gid FROM satellite_spatial \
                );" metadata
    /awips2/psql/bin/psql -U awips -c "DELETE FROM satellite_spatial \
        WHERE satellite_spatial.gid NOT IN ( \
            SELECT DISTINCT ON (the_geom) gid FROM satellite_spatial \
                );" metadata
}

# this method makes an assumption that coverage_gid will default to 1 and 2 
# this method also doesn't delete any ingested data
change_duplicates() {
    /awips2/psql/bin/psql -U awips -c "UPDATE satellite SET coverage_gid = 1 WHERE coverage_gid != 1;" metadata
    /awips2/psql/bin/psql -U awips -c "DELETE FROM satellite_spatial WHERE satellite_spatial.gid != 1;" metadata
}

while true; do
    #delete_duplicates
    change_duplicates
    sleep 1
done
