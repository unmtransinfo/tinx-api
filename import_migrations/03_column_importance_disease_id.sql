/* Create tinx_importance.disease_id and set to correct columns from tinx_disease.
 *
 * Does NOT create index. 
 */
START TRANSACTION;

alter table tinx_importance add column disease_id INT;

update tinx_importance 
  join tinx_disease 
    on tinx_disease.doid = tinx_importance.doid
set disease_id = tinx_disease.id;


COMMIT;
