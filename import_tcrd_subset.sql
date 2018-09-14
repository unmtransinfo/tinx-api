/* 
 * Place this script in the same directory as the uncompressed tcrd_subset.sql
 *
 * Then execute it with:
 *
 *     $ mysql -u root -p [DATABSE_NAME] < import_tcrd.subset.sql
 */
set global net_buffer_length=1000000;
set global max_allowed_packet=1000000000;

SET foreign_key_checks = 0;

source tcrd_subset.sql

SET foreign_key_checks = 1;
