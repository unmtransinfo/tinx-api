/* Create tinx_disease.id and index. */
START TRANSACTION;

alter table tinx_disease add column id int not null;
select @i := 0;
UPDATE tinx_disease SET id = (select @i := @i + 1);
create unique index tinx_disease_id on tinx_disease (id);

COMMIT;
