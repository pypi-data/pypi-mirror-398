# -*- coding: utf-8 -*-
"""
Csv based importation module

1 - Load csv file get headers
1 - Load sql columns of the current model

2 - Try auto-association
3 - Generate form
4 - Populate form (with auto-associated columns and optionnal loaded
association)
5- insert or update elements
"""
import csv

import transaction

try:
    from io import StringIO
except ImportError:
    from io import StringIO

from collections import OrderedDict

from pyramid_celery import celery_app
from sqla_inspect.base import BaseSqlaInspector
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, Numeric
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm import exc as sqlalchemy_exc
from sqlalchemy.schema import ColumnDefault

from caerp.celery.exception import MissingMandatoryArgument, MultipleInstanceFound
from caerp.celery.models import CsvImportJob
from caerp.celery.tasks import utils
from caerp.compute import math_utils
from caerp.utils import ascii
from caerp.utils.datetimes import str_to_date

logger = log = utils.get_logger(__name__)

MISSING_KEY_ERROR = "Erreur : Le champ {0} ({1}) est requis mais n'a pas été \
configuré à l'étape 2"
MULTIPLE_ENTRY_ERROR = "Pour une même valeur clé ({0}), plusieurs entrées \
ont été détectées, nous ne sommes pas en mesure de mettre à jour ces données."
NO_ENTRY_FOUND_ERROR = "Aucune entrée n'a pu être retrouvée pour la clé {0} \
avec la valeur {1}"
NO_ID_KEY_ERROR = "Une entrée n'a pas de valeur pour la clé {0}."
UNFILLED_VALUES = ("", None, 0)

BOOLEAN_FALSE = ("0", "false", "non", "", "False", "N", "Non", "NON", "NO")
DATETIME_FORMAT = "%d/%m/%Y"


DEFAULT_ID_LABEL = "Identifiant"
DEFAULT_DELIMITER = ";"
DEFAULT_QUOTECHAR = '"'
DELIMITERS = (";", ",", ":")
QUOTECHARS = ('"', '"')


MODELS_CONFIGURATION = {}


def format_input_value(value, sqla_column_dict, force_rel_creation=False):
    """
    format value to fetch the database storage expectations
    For example dates are input in dd/mm/yyyy format, we want datetime objects

    Relationship technics:

        ManyToOne relationship : we use the related_key (attribute of the
        related element) to find the related element we're supposed to point to

        OneToMany relationship: we use the related key (attribute of the
        related element) to instantiate a new related element. NB: It only
        works with related elements with one argument (typically list of dates
        ...)

    :param str value: The value coming from the csv file
    :param dict sqla_column_dict: The datas collected about the destination
    attribute
    :param bool force_rel_creation: Should we force the creation of a related
    element on import (default False), only in case of many to one
    relationships.  Note : the related_key attribute should be sufficient to
    create a new instance of the related element
    :returns: The formatted value
    :rtype: object (datetime) or string depending on the column
    """

    prop = sqla_column_dict["__col__"]

    res = value

    if isinstance(prop, RelationshipProperty):
        # Handle the relationship
        # Get the id of the corresponding model and return it
        if sqla_column_dict["rel_type"] == "manytoone":
            if "related_retriever" in sqla_column_dict:
                func = sqla_column_dict["related_retriever"]
                res = func(value, force_rel_creation)
            else:
                related_key = sqla_column_dict["related_key"]
                class_ = prop.mapper.class_
                # We query the database to get the corresponding element
                # filtering on the configured related_key
                res = (
                    class_.query().filter(getattr(class_, related_key) == value).first()
                )
                if res is None and force_rel_creation:
                    if value is not None and value.strip():
                        logger.debug(
                            "Creating a new element : %s %s" % (related_key, value)
                        )
                        creation_dict = {related_key: value}
                        res = class_(**creation_dict)
        else:
            # We have a one to many relationship, we generate an instance using
            # the related_key as instanciation attribute
            related_key = sqla_column_dict["related_key"]
            class_ = prop.mapper.class_
            if "formatter" in sqla_column_dict:
                value = sqla_column_dict["formatter"](value)
            args = {related_key: value}
            res = [class_(**args)]

    else:
        column = prop.columns[0]
        column_type = getattr(column.type, "impl", column.type)

        if "formatter" in sqla_column_dict:
            res = sqla_column_dict["formatter"](value)

        elif isinstance(column_type, Boolean):
            if value in BOOLEAN_FALSE:
                res = False
            else:
                res = True

        elif isinstance(
            column_type,
            (
                DateTime,
                Date,
            ),
        ):
            res = str_to_date(value)

        elif isinstance(column_type, (Integer, BigInteger)):
            res = math_utils.str_to_int(value, default=None)
        elif isinstance(column_type, (Numeric, Float)):
            res = math_utils.str_to_float(value, default=None)
    return res


class CsvImportAssociator(BaseSqlaInspector):
    """
    An importation tool used to associate csv datas to a destination dict

    Collect datas from a sqlalchemy model
    Generate a guessed association_dict from a list of field names

    for column in columns:
        if column:
            store_name_and_title
        else:
            store_name_title_and_values_if_appoption
    """

    config_key = "import"

    def __init__(self, model, excludes=()):
        BaseSqlaInspector.__init__(self, model)
        self.model = model
        self.excludes = excludes
        self.columns = self._collect_columns()

    def _collect_columns(self):
        """
        Collect the columns names and titles to be able to generate a
        importation form or guess associations
        """
        result = OrderedDict()
        todrop = []
        for prop in self.get_sorted_columns():
            if prop.key in self.excludes:
                continue
            info_dict = self.get_info_field(prop)
            colanderalchemy_infos = info_dict.get("colanderalchemy", {})

            import_dict = info_dict.get(self.config_key, {})

            ui_label = colanderalchemy_infos.get("title", prop.key)
            datas = {"name": prop.key, "label": ui_label, "__col__": prop}
            datas.update(import_dict)

            if isinstance(prop, RelationshipProperty):
                if prop.uselist:
                    # A one to many relationship
                    if "related_key" not in datas:
                        logger.debug("Missing infos about a relationship %s" % prop.key)
                        continue
                    datas["rel_type"] = "onetomany"
                else:
                    # A many to one relationship
                    datas.setdefault("related_key", "label")
                    # We can drop the foreignky column from the importable
                    # columns to avoid misunderstanding
                    todrop.append("%s_id" % prop.key)
                    datas["rel_type"] = "manytoone"
            else:
                column = prop.columns[0]
                if not isinstance(column.default, ColumnDefault):
                    if not column.nullable and prop.key != "id":
                        datas["mandatory"] = True

            result[datas["name"]] = datas

        for key in todrop:
            if key in result:
                ui_label = result[key].get("label")
                rel_key = key[:-3]
                if rel_key in result:
                    result[rel_key]["label"] = ui_label
                if result[key].get("mandatory"):
                    result[rel_key]["mandatory"] = True
                result.pop(key)
        return result

    def get_columns(self):
        """
        A simple getter
        """
        return self.columns

    def guess_association_dict(self, csv_datas_headers, user_defined=None):
        """
        Try to build an association dict between the header of the current csv
        file we want to import and the model we want to generate

        :param dict user_defined: An already defined association_dict we want
        to use as reference

        :returns: a dict with {headername: associated_column}
        :rtype: dict that's pickable (can be stored in the session)
        """
        result = OrderedDict()
        for header in csv_datas_headers:
            header = ascii.force_unicode(header)
            if not header:
                continue
            result[header] = None
            toguess = header.replace("*", "").lower()
            for column in list(self.columns.values()):
                name = column["name"].lower()
                label = column["label"].lower()
                if toguess in [name, label]:
                    result[header] = column["name"]

        if user_defined is not None:
            for key, value in list(user_defined.items()):
                if key in result:
                    result[key] = value

        return result

    def check_association_dict(self, association_dict=None):
        """
        Check that the provided association dict fills mandatory arguments

        :TypeError MissingMandatoryArgument: if mandatory argument is missing
            and id is in the provided keys
        """
        if association_dict is None:
            association_dict = self.association_dict
        values = list(association_dict.values())
        if "id" not in values:
            for column in list(self.columns.values()):
                if column.get("mandatory"):
                    if column["name"] not in values:
                        raise MissingMandatoryArgument(
                            MISSING_KEY_ERROR.format(column["label"], column["name"])
                        )

    def set_association_dict(self, association_dict):
        """
        Set the association dict that will be used

        :param dict association_dict: a {csv_key: model_attribute_name} dict
        """
        self.association_dict = association_dict

    def collect_args(self, csv_line, force_rel_creation=False):
        """
        Collect the arguments to be used to build the new model
        * get the value from the csv_line
        * format it thanks to the informations provided in the column info attr
        * place it in a new dict with the model attribute names as keys

        :param dict line: a csv line as a dict
        :param bool force_rel_creation: Should we try to build related
        configuration option on the fly ?
        :returns: a tuple with the args to be used for instanciation and the
            resting values
        """
        kwargs = {}
        unhandled = {}
        for csv_key, value in list(csv_line.items()):
            value = ascii.force_unicode(value)

            if csv_key == "id":
                if not value:
                    column_name = None
                else:
                    column_name = "id"
            else:
                key = ascii.force_unicode(csv_key)
                column_name = self.association_dict.get(key)
                if column_name is None:
                    column_name = self.association_dict.get(csv_key)

            if column_name is None:
                unhandled[csv_key] = value

            else:
                column = self.columns.get(column_name)
                if column is not None:
                    new_value = format_input_value(
                        value,
                        column,
                        force_rel_creation,
                    )
                    if new_value is not None:
                        kwargs[column_name] = new_value
                    else:
                        unhandled[csv_key] = value
                else:
                    kwargs[column_name] = value
        return kwargs, unhandled


def get_csv_reader(
    csv_buffer,
    delimiter=DEFAULT_DELIMITER,
    quotechar=DEFAULT_QUOTECHAR,
):
    return csv.DictReader(
        csv_buffer,
        delimiter=str(delimiter),
        quotechar=str(quotechar),
    )


class CsvImporter(object):
    """
    A csv datas importer

    * Should handle update if an id is provided
    * Should format values when generating add/update arguments
    * Should check mandatory arguments
    * Should return imported fields with errors
    * Should return non-imported datas with the appropriate id

    auto-compute relationship values
    auto-find which fields are imported

    :param class dbssession: The dbsession to use for import
    :param class factory: The type of model we want to import
    :param obj csv_buffer: A file buffer containing csv datas
    :param obj association_handler: The object handling the association
        between csv fields and model attributes
    :param str action: The action to be performed on import

            * insert: insertion of the fields is performed
            * update: we update the fields if an id key matches an existing
              object
            * override: we override the datas if an id keys matches an existing
              object
            * only_update: we update the fields if an id key matches an
            existing object and don't insert new entries
            * only_override: we override the datas if an id keys matches an
              existing object and don't insert new entries

    :param int id_key: The id key to be used (by default, we use the model's id
        to identify duplicate entries, else, we can use an external id

    :param bool force_rel_creation: Force the creation of related configuration
    elements ?

    :param dict default_values: Default arguments used to initialize new
    entries
    :param list callbacks: list of callbacks launched after importation each
    callback should take the following arguments

        action
        dbsession
        model
        updated
        args

    Usage:

        association_handler = CsvImportAssociator(UserDatas)
        importer = CsvImporter(DbSession(), UserDatas, file('users.csv', 'r'),
    """

    delimiter = ";"
    quotechar = '"'

    def __init__(
        self,
        dbsession,
        factory,
        csv_buffer,
        association_handler,
        action="only_update",
        id_key="id",
        force_rel_creation=False,
        default_values=None,
        delimiter=DEFAULT_DELIMITER,
        quotechar=DEFAULT_QUOTECHAR,
        callbacks=(),
    ):
        self.dbsession = dbsession
        self.factory = factory
        self.association_handler = association_handler
        self.in_error_lines = []
        self.unhandled_datas = []
        self.imported = []
        self.messages = []
        self.err_messages = []
        self.new_count = 0
        self.update_count = 0

        if action not in (
            "insert",
            "update",
            "override",
            "only_update",
            "only_override",
        ):
            raise KeyError(
                "The action attr should be one of " '("insert", "update", "override")'
            )

        if action == "insert":
            self.association_handler.check_association_dict()

        self.action = action
        self.id_key = id_key
        self.force_rel_creation = force_rel_creation
        self.default_init_values = default_values or {}

        self.quotechar = str(quotechar)
        self.delimiter = str(delimiter)
        self.csv_reader = get_csv_reader(csv_buffer, self.delimiter, self.quotechar)
        # Importation callbacks launched after each successfull import line
        # action
        self.callbacks = callbacks

    def import_datas(self, persist=True):
        """
        Import the datas provided in the csv_buffer as factory objects

        :param bool fake: Should datas be persisted to the database (default
        True)
        """
        for line in self.csv_reader:
            model, message = self.import_line(line, persist=persist)
            if model is None:
                self.err_messages.append(message)
            elif message is not None:
                self.messages.append(message)

        if persist:
            new_entry_msg = "{0} nouvelles entrées ont été traitées"
            update_entry_msg = "{0} entrées existantes ont été traitées"
        else:
            new_entry_msg = "{0} nouvelles entrées seront créées"
            update_entry_msg = "{0} entrées existantes seront mises à jour"

        self.messages.append(new_entry_msg.format(self.new_count))
        self.messages.append(update_entry_msg.format(self.update_count))

    def _insert(self, args, persist=True):
        """
        Insert an instance in the database

        :param dict args: The args used to instanciate our new model
        :returns: a tuple (model, updated_token) where updated_token is a
        boolean saying if it's an update
        """
        logger.debug("Inserting (1) {}".format(args))
        for key, value in list(self.default_init_values.items()):
            args[key] = value

        logger.debug("Inserting {}".format(args))
        if "id" in args:
            args.pop("id")
        model = self.factory(**args)
        if persist:
            self.dbsession.add(model)
            self.dbsession.flush()
        return model, False

    def _update(self, args, override=False, persist=True, insert=True):
        """
        Update an element in the database or insert one if no id is provided

        :param dict args: The args used to update the model
        :param bool override: should we override the existing datas ?
        :raises: sqlalchemy insert or update errors
        :returns: a tuple (model, updated_token) where updated_token is a
        boolean saying if it's an update
        """
        logger.debug("Launching update")
        logger.debug("Args :")
        logger.debug(args)
        logger.debug("Insert ? : %s" % insert)
        identification_value = args.pop(self.id_key, None)
        updated = False

        if identification_value in UNFILLED_VALUES:
            # No identification value is provided
            if not insert:
                raise MultipleInstanceFound(
                    NO_ID_KEY_ERROR.format(
                        self.id_key,
                    )
                )
            model, updated = self._insert(args, persist=persist)

        else:
            identification_column = getattr(self.factory, self.id_key)

            try:
                model = (
                    self.factory.query()
                    .filter(identification_column == identification_value)
                    .one()
                )

                for key, value in list(self.default_init_values.items()):
                    if getattr(model, key) != value:
                        log.warn("POSSIBLE BREAK IN ATTEMPT")
                        log.warn("Importation process, default values :")
                        log.warn(self.default_init_values)
                        log.warn("The model they try to edit : %s" % model.id)
                        raise Exception("POSSIBLE BREAK IN ATTEMPT !!!!!!")

                for key, value in list(args.items()):
                    if getattr(model, key) in UNFILLED_VALUES or override:
                        setattr(model, key, value)
                if persist:
                    model = self.dbsession.merge(model)
                    self.dbsession.flush()
                updated = True

            except sqlalchemy_exc.NoResultFound:
                if not insert:
                    raise MultipleInstanceFound(
                        NO_ENTRY_FOUND_ERROR.format(self.id_key, identification_value)
                    )
                # We first restore the poped identification column (if it's not
                # the id key: id key should not be set but email can be used as
                # identification key and should be set for new entries)
                if self.id_key != "id":
                    args[self.id_key] = identification_value
                model, updated = self._insert(args, persist=persist)

            except sqlalchemy_exc.MultipleResultsFound:
                raise MultipleInstanceFound(
                    MULTIPLE_ENTRY_ERROR.format(identification_value)
                )

        return model, updated

    def _only_update(self, args, persist=True):
        """
        Update an element completing its attributes
        :param dict args: The args used to update the model
        :returns: a tuple (model, updated_token) where updated_token is a
        boolean saying if it's an update
        """
        return self._update(args, override=False, persist=persist, insert=False)

    def _override(self, args, persist=True):
        """
        Update an element overriding attributes with the newly provided values
        or insert a new one if no id is provided

        :param dict args: The args used to update the model
        :returns: a tuple (model, updated_token) where updated_token is a
        boolean saying if it's an update
        """
        return self._update(args, override=True, persist=persist)

    def _only_override(self, args, persist=True):
        """
        Update an element overriding attributes with the newly provided values

        :param dict args: The args used to update the model
        :returns: a tuple (model, updated_token) where updated_token is a
        boolean saying if it's an update
        """
        return self._update(args, override=True, persist=persist, insert=False)

    def launch_callbacks(self, model, updated, args):
        """
        Launch import callbacks for the given model

        :param obj model: The current managed model
        :param bool updated: Has the model been updated
        :param dict args: The importation arguments
        """
        for callback in self.callbacks:
            callback(
                self.action,
                self.dbsession,
                model,
                updated,
                args,
            )

    def import_line(self, line, persist=True):
        """
        Import one line of a csv file
        :returns: a duple with the newly_created model (or None) and a
            message
        """
        message = None
        args, unhandled_columns = self.association_handler.collect_args(
            line,
            self.force_rel_creation,
        )

        function = getattr(self, "_{0}".format(self.action))
        logger.debug("The function we use : %s" % function)
        # Here we should handle edition
        try:
            model, updated = function(args, persist=persist)
            self.imported.append(model)
            unhandled_columns[DEFAULT_ID_LABEL] = model.id
            self.unhandled_datas.append(unhandled_columns)
            res = model
            if updated:
                self.update_count += 1
            else:
                self.new_count += 1
            if persist:
                self.launch_callbacks(model, updated, args)
        except OperationalError as error:
            import traceback

            traceback.print_exc()
            res = None
            self.in_error_lines.append(line)
            message = (
                "Erreur d'intégrité des données au lancement de la "
                "requête {} avec les paramètres {}".format(
                    error.statement, error.params
                )
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            log.exception("Erreur lors de l'import de données")
            self.in_error_lines.append(line)
            res = None
            message = str(e)
        return res, message

    def gen_csv_str(self, datas):
        """
        Generate a csv string with the given datas

        :param list datas: a list of dict representing csv rows
        :returns: a csv string
        :rtype: str
        """
        if not datas:
            result = ""
        else:
            buf = StringIO()
            fieldnames = [key for key in list(datas[0].keys()) if key != ""]
            writer = csv.DictWriter(
                buf,
                fieldnames,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                extrasaction="ignore",
                quoting=csv.QUOTE_ALL,
            )
            writer.writeheader()
            datas = ascii.to_utf8(datas)
            writer.writerows(datas)
            result = buf.getvalue()
        return result

    def log(self):
        """
        return the datas we want to log in the database (see
        models.job.CsvImportJob)
        """
        unhandled_datas_csv = self.gen_csv_str(self.unhandled_datas)
        in_error_lines_csv = self.gen_csv_str(self.in_error_lines)
        result = dict(
            unhandled_datas_csv=unhandled_datas_csv,
            in_error_lines_csv=in_error_lines_csv,
            messages=self.messages,
            error_messages=self.err_messages,
            status="done",
        )
        return result


def get_csv_importer(
    dbsession,
    model_type,
    csv_buffer,
    association_handler,
    action="insert",
    id_key="id",
    force_rel_creation=False,
    default_values=(),
    delimiter=DEFAULT_DELIMITER,
    quotechar=DEFAULT_QUOTECHAR,
):
    factory = MODELS_CONFIGURATION[model_type]["factory"]
    callbacks = MODELS_CONFIGURATION[model_type]["callbacks"]
    return CsvImporter(
        dbsession,
        factory,
        csv_buffer,
        association_handler,
        action,
        id_key,
        force_rel_creation,
        default_values,
        delimiter,
        quotechar,
        callbacks=callbacks,
    )


def get_csv_import_associator(key):
    """
    Build a csv import associator regarding the provided model
    """
    return CsvImportAssociator(
        MODELS_CONFIGURATION[key]["factory"], MODELS_CONFIGURATION[key]["excludes"]
    )


# Here we use the bind argument so that the task will be attached as a bound
# method and thus we can access attributes like request
@celery_app.task(bind=True)
def async_import_datas(
    self,
    model_type,
    job_id,
    association_dict,
    csv_filepath,
    id_key,
    action,
    force_rel_creation,
    default_values,
    delimiter,
    quotechar,
):
    """
    Launch the import of the datas provided in the csv_filepath

    :param str model_type: A handled model_type
    :param int job_id: The id of the db job object that should handle the
        return datas
    :param dict association_dict: describes the association
        csv_key<->SQLA model attribute
    :param str csv_filepath: The absolute path to the csv file
    :param str id_key: The model attribute used to handle updates
    :param str action: The name of the action we want to run
        (insert/update/override/only_update/only_override)
    :param bool force_rel_creation: Force the creation of configurable related
    elements
    :param default_values: default_values used to initialize new objects
    :param delimiter: The delimiter to use for csv parsing
    :param quotechar: The quotechar to use for csv parsing
    """
    logger.info("We are launching an asynchronous csv import")
    logger.info("  The job id : %s" % job_id)
    logger.info("  The csv_filepath : %s" % csv_filepath)
    logger.info("  The association dict : %s" % association_dict)
    logger.info("  The id key : %s" % id_key)
    logger.info("  Action : %s" % action)
    logger.info("  Default initialization values : %s" % default_values)

    utils.start_job(self.request, CsvImportJob, job_id)

    from caerp.models.base import DBSESSION

    try:
        associator = get_csv_import_associator(model_type)
        associator.set_association_dict(association_dict)
        csv_buffer = open(csv_filepath, "r")
        importer = get_csv_importer(
            DBSESSION(),
            model_type,
            csv_buffer,
            associator,
            action=action,
            id_key=id_key,
            force_rel_creation=force_rel_creation,
            default_values=default_values,
            delimiter=delimiter,
            quotechar=quotechar,
        )
        logger.info("Importing the datas")
        importer.import_datas()
        transaction.commit()
    except Exception as e:
        transaction.abort()
        logger.exception("The transaction has been aborted")
        utils.record_failure(CsvImportJob, job_id, [e])
    else:
        logger.info("We update the job informations")
        utils.record_completed(CsvImportJob, job_id, **importer.log())
    return ""
