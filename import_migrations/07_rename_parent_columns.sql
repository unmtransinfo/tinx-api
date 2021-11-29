/* Rename, retype some columns. 
 */

START TRANSACTION;

alter table do_parent change `parent` parent varchar(12);
alter table dto change `dtoid` id varchar(255);
alter table dto change `parent_id` parent varchar(255);

update dto set parent = replace(parent, ':', '_');

COMMIT;
