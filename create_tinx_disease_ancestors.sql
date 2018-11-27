/* create_tinx_disease_ancestors.sql
 *
 * Creates the table tinx_disease_ancestors which contains a set of adjacency
 * lists expressing paths from root nodes to each individual disease.
 */

/* Indexes for performance. Note that do_parent.doid is not unique and cannot
 * be a primary key. */
CREATE INDEX do_parent_doid_idx ON do_parent (doid);
CREATE INDEX do_parent_parent_idx ON do_parent (parent);
CREATE INDEX tinx_disease_doid_idx ON tinx_disease (doid);

/* Create the table. We assume a max depth of 14. (The longest observed was 10) */
CREATE TABLE tinx_disease_ancestors (
  doid            VARCHAR(255) NOT NULL,
  max_ancestor    VARCHAR(255) NOT NULL,
  ancestor_path   TEXT NOT NULL,
  KEY (doid),
  KEY (max_ancestor)
) SELECT
  p1.doid AS doid,
  COALESCE(p14.doid, p13.doid, p12.doid, p10.doid, p9.doid, p8.doid, p7.doid, p6.doid, p5.doid, p4.doid, p3.doid, p2.doid, p1.doid) AS max_ancestor,
  CONCAT_WS(' / ', p14.doid, p13.doid, p12.doid, p10.doid, p9.doid, p8.doid, p7.doid, p6.doid, p5.doid, p4.doid, p3.doid, p2.doid, p1.doid) AS ancestor_path
FROM do_parent p1
LEFT JOIN do_parent p2 ON p2.doid = p1.parent
LEFT JOIN do_parent p3 ON p3.doid = p2.parent
LEFT JOIN do_parent p4 ON p4.doid = p3.parent
LEFT JOIN do_parent p5 ON p5.doid = p4.parent
LEFT JOIN do_parent p6 ON p6.doid = p5.parent
LEFT JOIN do_parent p7 ON p7.doid = p6.parent
LEFT JOIN do_parent p8 ON p8.doid = p7.parent
LEFT JOIN do_parent p9 ON p9.doid = p8.parent
LEFT JOIN do_parent p10 ON p10.doid = p9.parent
LEFT JOIN do_parent p11 ON p11.doid = p10.parent
LEFT JOIN do_parent p12 ON p12.doid = p11.parent
LEFT JOIN do_parent p13 ON p13.doid = p12.parent
LEFT JOIN do_parent p14 ON p14.doid = p13.parent;


ALTER TABLE tinx_disease_metadata
ADD COLUMN category TEXT;

UPDATE tinx_disease_metadata
NATURAL JOIN tinx_disease
LEFT JOIN tinx_disease_ancestors ancestors ON ancestors.doid = tinx_disease.doid
JOIN tinx_disease d2 ON d2.doid = ancestors.max_ancestor
SET category = d2.name;

