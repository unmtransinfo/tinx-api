/* add_metadata_tables.sql
 *
 * Creates metadata tables to store cached data for display in the TIN-X app.
 * The computed metadata includes the count of important targets per disease
 * and the count of important disease per target -- all derivable from the
 * database, but slow to compute.
 *
 * This script also creates the nds_rank table, which will be populated by a
 * separate python script.
 */

START TRANSACTION;

/* Important targets per disease. */
DROP TABLE IF EXISTS tinx_disease_metadata;
CREATE TABLE IF NOT EXISTS tinx_disease_metadata (
  id INT AUTO_INCREMENT,
  tinx_disease_id INT,
  num_important_targets INT,
  PRIMARY KEY (id),
  FOREIGN KEY (tinx_disease_id) REFERENCES tinx_disease (id)
) SELECT
    tinx_disease.id AS tinx_disease_id,
    COUNT(tinx_importance.id)  AS num_important_targets
  FROM tinx_disease
  LEFT JOIN tinx_importance ON tinx_importance.disease_id = tinx_disease.id
  GROUP BY tinx_disease.id;

/* Important diseases per protein. */
DROP TABLE IF EXISTS protein_metadata;
CREATE TABLE IF NOT EXISTS protein_metadata (
  id INT AUTO_INCREMENT,
  protein_id INT,
  num_important_diseases INT,
  PRIMARY KEY (id),
  FOREIGN KEY (protein_id) REFERENCES protein (id)
) SELECT
    protein.id AS protein_id,
    COUNT(tinx_importance.id) AS num_important_diseases
  FROM protein
  LEFT JOIN tinx_importance ON tinx_importance.protein_id = protein.id
  GROUP BY protein.id;

/* Currently empty. This will be populated by a python script. */
CREATE TABLE IF NOT EXISTS tinx_nds_rank (
  id                 INT NOT NULL AUTO_INCREMENT,
  tinx_importance_id INT,
  rank               INT,
  PRIMARY KEY (id),
  FOREIGN KEY (tinx_importance_id) REFERENCES tinx_importance (id)
);

COMMIT;
