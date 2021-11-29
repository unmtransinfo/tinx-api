/* Adds foreign key constraing tinx_importance.disease_id -> tinx_disease.id */
START TRANSACTION;

ALTER TABLE tinx_importance
  ADD CONSTRAINT tinx_importance_disease_id_fk
FOREIGN KEY (disease_id) REFERENCES tinx_disease (id);

COMMIT;
