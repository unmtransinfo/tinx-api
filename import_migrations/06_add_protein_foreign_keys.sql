/* changes type of protein.dtoid to varchar(255)
 * Adds foreign key protein.dtoid references dto.dtoid */

START TRANSACTION;

ALTER TABLE protein MODIFY COLUMN dtoid varchar(255) COLLATE utf8_unicode_ci;

UPDATE protein SET dtoid = REPLACE(dtoid, ':', '_');
UPDATE dto SET dtoid = REPLACE(dtoid, ':', '_');

/* Weird proteins that aren't correctly mapped to a dtoid. */
UPDATE protein SET dtoid = NULL WHERE name IN ('NOX1_HUMAN', 'NOX5_HUMAN');

ALTER TABLE protein ADD CONSTRAINT protein_dtoid_fk FOREIGN KEY (dtoid) REFERENCES dto(dtoid);

COMMIT;
