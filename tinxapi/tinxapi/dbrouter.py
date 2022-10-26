class DatabaseRouter(object):

    def db_for_read(self, model, **hints):
        """
        What database should be used for reading the given model?

        :param model:
        :param hints:
        :return:
        """
        if hasattr(model, 'tcrd_meta') and model.tcrd_meta:
            return 'tcrd_meta'
        elif hasattr(model, 'tcrd_model') and model.tcrd_model:
            return 'tcrd'
        else:
            return None

    def db_for_write(self, model, **hints):
        """
        What database should be used for writes to the given model?

        :param model:
        :param hints:
        :return:
        """
        if hasattr(model, 'tcrd_model') and model.tcrd_model:
            raise Exception("This model is read only.")
        else:
            return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Should Django try to run migrations for the given model?

        This is written fairly verbosely, but for sake of clarity. No migrations
        are allowed on tcrd, and only certain models are allowed to be migrated on
        default (e.g., we don't want it creating tcrd models in default).

        :param db: Name of the database
        :param app_label:
        :param model_name: Name of the model
        :param hints:
        :return: True if the migration is allowed, false otherwise.
        """
        if db == 'tcrd':
            return False
        elif db == 'tcrd_meta':
            return model_name in ['proteinmetadata', 'diseasemetadata']
        elif db == 'default':
            return model_name in ['logentry', 'permission', 'group', 'user', 'session', 'contenttype']
        else:
            return False

    def allow_relation(self, obj1, obj2, **hints):
        return True
