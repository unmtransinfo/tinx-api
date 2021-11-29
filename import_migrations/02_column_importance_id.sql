/* Create tinx_importance.id and index. */

START TRANSACTION;

select @i := 0;
alter table tinx_importance add column id int not null;
UPDATE tinx_importance SET id = (select @i := @i + 1);
create unique index tinx_importance_id on tinx_importance (id);

COMMIT;
