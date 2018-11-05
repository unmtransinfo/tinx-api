# compute_nds_rank.py
#
# Computes the NDS rank for each target in the context of each disease and
# stores that data in the database.
#
# NDS (non-dominated solution) ranking is employed within TIN-X as a method of
# determining which points are the most interesting to show to the user.
#
# To oversimplify: The most interesting points are those that are on the
# northeastern edge of the plot, followed by those that would be on the
# norhteastern edge if the actual northeastern edge were removed, and so on.
#
# Codifying this mathematically: We seek to identify a non-dominated solution
# (NDS) to the multi-objective optimization problem of maximizing both
# importance and novelty. That is, we will find a subset of points which
# "dominate" all other points in the plot. We say that a point x1 dominates a
# point x2 if x1 is no worse than x2 in all objectives and if x1 is strictly
# better than x2 in at least one objective. After identifying an NDS, we then
# remove the NDS from the plot -- assigning each point in the NDS the rank 1
# -- and then find an NDS for the remaining points, which we assign the rank 2.
# This process is then repeated until all points have been ranked.
#
# The algorithm is arguably simpler than the explanation:
#
#   1. Let current_rank := 1. Let max_novelty := null.
#
#   2. Iterate through all remaining points by descending importance. For each:
#
#       2.1. If the novelty of the point is greater than max_novelty, or if
#            max_novelty is null, then assign the point the rank current_rank,
#            set max_novelty to the novelty score of this point, and remove the
#            point from the set of remaining points.
#
#   3. If there are remaining points that do not have an assigned rank, then
#      increment current_rank, reset max_novelty to null, and repeat step 2.
#
#
# Usage:
#    python compute_nds_rank.py [database_name] [host_name]

import MySQLdb
import getpass
import sys

import tinxapi.tinxapi.secrets as secrets

# Print progress bar. Adapted from:
# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '#'):
  """
  Call in a loop to create terminal progress bar
  @params:
      iteration   - Required  : current iteration (Int)
      total       - Required  : total iterations (Int)
      prefix      - Optional  : prefix string (Str)
      suffix      - Optional  : suffix string (Str)
      decimals    - Optional  : positive number of decimals in percent complete (Int)
      length      - Optional  : character length of bar (Int)
      fill        - Optional  : bar fill character (Str)
  """
  percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
  filledLength = int(length * iteration // total)
  bar = fill * filledLength + '-' * (length - filledLength)
  sys.stdout.write('\r%s |%s| %s%% %s\r' % (prefix, bar, percent, suffix))
  sys.stdout.flush()
  # Print New Line on Complete
  if iteration == total:
    sys.stdout.write('\n')


database = sys.argv[1] if len(sys.argv) > 1 else 'tcrd'
hostname = sys.argv[2] if len(sys.argv) > 2 else 'localhost'

print('+----------------------------------------------------------+')
print('| compute_nds_rank.py                                      |')
print('|                                                          |')
print('| This script computes the NDS rank of each disease-target |')
print('| association and stores it in the database.               |')
print('|                                                          |')
print('| You will be prompted to enter the username and password  |')
print('| for a database user with permission to write to the      |')
print('| database you have specified.                             |')
print('|                                                          |')
print('| Usage:                                                   |')
print('|   python compute_nds_rank.py [database] [hostname]       |')
print('|                                                          |')
print('| Database: {:46s} |'.format(database))
print('| Hostname: {:46s} |'.format(hostname))
print('+----------------------------------------------------------+')
print('')

username = raw_input('MySQL username: ')
password = getpass.getpass(prompt = 'MySQL password: ')

print('')
sys.stdout.write('Establishing database connection ... ')
sys.stdout.flush()

try:
  db_connection = MySQLdb.connect(hostname, username, password, database)
except Exception as e:
  print('')
  print("Can't connect to database")
  print(e)
  exit(1)

cursor = db_connection.cursor()

sys.stdout.write(' done.\n\n')
sys.stdout.write('Retrieving list of diseases ... ')
sys.stdout.flush()

cursor.execute("SELECT id FROM tinx_disease")
diseases = cursor.fetchall()
print('done.')
disease_cnt = len(diseases)
print('Found {} total diseases.'.format(disease_cnt))

print('')
sys.stdout.write('Determining total number of datapoints to rank ... ')
sys.stdout.flush()
cursor.execute("SELECT COUNT(*) FROM tinx_importance")
points_to_score = cursor.fetchone()[0]
print('done.')
print('Found {} total disease-target associations to rank.'.format(points_to_score))

print('')
sys.stdout.write('Truncating tinx_nds_rank ... ')
sys.stdout.flush()
cursor.execute("TRUNCATE TABLE tinx_nds_rank")
print('done.')

print('')
print('Computing NDS ranks ...')

def get_datapoints_for_disease(disease_id):
  """
  Retrieves all datapoints (associated targets) for the specified disease as
  an array of tuples, where each tuple is of the form (tinx_importance.id,
  novelty, importance). The returned datapoints will be sorted in descending
  order by importance.

  :param disease_id:  The ID of the disease for which to retrieve data.
  :return: An array of tuples.
  """
  cursor.execute("""
    SELECT
      tinx_importance.id,
      tinx_novelty.score AS novelty,
      tinx_importance.score AS importance
    FROM tinx_importance
    JOIN tinx_novelty ON tinx_importance.protein_id = tinx_novelty.protein_id
    WHERE tinx_importance.disease_id = %s
    ORDER BY importance DESC""", (disease_id, ))
  return cursor.fetchall()


def bin_into_fronts(disease_id):
  """
  Determine the NDS rank of each target associated with the specified disease
  and return a dictionary mapping tinx_importance.id to the new rank.

  :param disease_id: The disease for which to compute NDS ranks.
  :return: A dictionary mapping ID's to the new ranks to assign.
  """
  datapoints = list(get_datapoints_for_disease(disease_id))
  front = 1
  max_novelty = None
  ret = dict()
  last_visited = 0

  while len(datapoints) > 0:
    # Note: This imperative approach was found to be significantly faster than
    # using next / enumerate
    index_to_remove = None
    v = None
    for i in range(last_visited, len(datapoints)):
      if max_novelty is None or datapoints[i][1] > max_novelty:
        index_to_remove = i
        v = datapoints[i]
        break

    if index_to_remove is None:
      # We've run out of points. Move on to the next front
      front += 1
      max_novelty = None
      last_visited = 0
    else:
      # We found a point with a bigger novelty. Assign it a rank
      max_novelty = v[1]
      ret[v[0]] = front
      del datapoints[index_to_remove]
      last_visited = index_to_remove

  return ret


def update_ranks(updates):
  """
  Inserts a row into tinx_nds_rank for each entry in the provided dictionary.

  :param updates: A dictionary mapping tinx_importance_id to the desired rank.
  :return:
  """
  cursor.executemany("""
    INSERT INTO tinx_nds_rank (tinx_importance_id, rank)
    VALUES (%s, %s)""", updates.items())

# Print the inital (0%) progress bar
printProgressBar(0, points_to_score, prefix = 'Progress:', suffix = 'Complete', length = 50)

# Number of points ranked so far
points_ranked = 0

for i in range(0, disease_cnt):
  updates = bin_into_fronts(diseases[i][0])
  points_ranked += len(updates)
  update_ranks(updates)
  printProgressBar(points_ranked, points_to_score,
                   prefix = 'Progress:',
                   suffix = 'Complete [Working on disease {} of {}]'.format(i, disease_cnt),
                   length = 50)

print('')
sys.stdout.write('Committing changes ... ')
sys.stdout.flush()
db_connection.commit()
print('done.')

print('')
print('Computation of NDS rank successful for all disease-target associations.')
