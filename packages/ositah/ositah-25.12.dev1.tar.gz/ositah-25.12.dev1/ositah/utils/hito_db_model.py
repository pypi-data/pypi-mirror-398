"""
Module defining the DB SQLAlchemy model.
This is done by using the class provided by Flask-sqlalchemy that requires the DB connection
to be initialized before. Thus this module must not be imported before it is done.
"""

from hito_tools.utils import sql_longtext_to_list

from ositah.utils.hito_db import new_uuid
from ositah.utils.utils import GlobalParams

global_params = GlobalParams()
db = global_params.hito_db

team_mgrs = db.Table(
    "team_agent",
    db.Column("team_id", db.String, db.ForeignKey("team.id")),
    db.Column("agent_id", db.String, db.ForeignKey("agent.id")),
)

children_team_mgrs = db.Table(
    "agent_team_parent_responsable",
    db.Column("team_id", db.String, db.ForeignKey("team.id")),
    db.Column("agent_id", db.String, db.ForeignKey("agent.id")),
)

activity_teams = db.Table(
    "activite_team",
    db.Column("activite_id", db.String, db.ForeignKey("activite.id")),
    db.Column("team_id", db.String, db.ForeignKey("team.id")),
)

project_teams = db.Table(
    "projet_team",
    db.Column("projet_id", db.String, db.ForeignKey("projet.id")),
    db.Column("team_id", db.String, db.ForeignKey("team.id")),
)


class Agent(db.Model):
    id = db.Column(db.String, primary_key=True)
    nom = db.Column(db.String)
    prenom = db.Column(db.String)
    email = db.Column(db.String)
    email_auth = db.Column(db.String)
    roles = db.Column(db.Text)
    statut = db.Column(db.String)
    team_id = db.Column(db.String)

    # Teams an agent is directly managing
    teams = db.relationship("Team", secondary=team_mgrs, backref=db.backref("managers"))

    # Children teams of the teams an agent is managing
    children_teams = db.relationship(
        "Team", secondary=children_team_mgrs, backref=db.backref("children_managers")
    )

    def __repr__(self):
        if self.email_auth is None or len(self.email_auth) == 0:
            connexion_email = self.email
        else:
            connexion_email = self.email_auth
        return (
            f"<Agent(nom={self.nom}, email={self.email}, roles={sql_longtext_to_list(self.roles)}"
            f" (email connexion={connexion_email}))>"
        )


class Carriere(db.Model):
    id = db.Column(db.String, primary_key=True)
    date_debut = db.Column(db.DateTime)
    date_fin = db.Column(db.DateTime)
    type = db.Column(db.String)
    agent_id = db.Column(db.String(36), db.ForeignKey("agent.id"), nullable=False)

    def __repr__(self):
        date = ""
        if self.date_debut:
            date += f" date_debut={self.date_debut}"
        if self.date_fin:
            date += f" date_debut={self.date_fin}"
        return f"<Carriere(id={self.id}, type={self.type}{date})>"


class Team(db.Model):
    id = db.Column(db.String, primary_key=True)
    nom = db.Column(db.String)
    description = db.Column(db.String)
    parent_team_id = db.Column(db.String)

    def __repr__(self):
        if not self.description or len(self.description) == 0:
            description = self.nom
        else:
            description = self.description
        return f"<Team(nom={self.nom}, description={description})>"


class Referentiel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String)
    ordre = db.Column(db.Integer)
    object_class = db.Column("class", db.String)

    def __repr__(self):
        return f"Referentiel<id={self.id}, libelle={self.libelle}, class={self.object_class}>"


class Activite(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_uuid)
    libelle = db.Column(db.String)
    description = db.Column(db.String)
    ordre = db.Column(db.Integer)

    activite_nsip_referentiel_id = db.Column(db.String, db.ForeignKey("referentiel.id"))
    projet_nsip_referentiel_id = db.Column(db.String, db.ForeignKey("referentiel.id"))

    referentiel_nsip_project = db.relationship(
        "Referentiel",
        backref=db.backref("activite_project", lazy=True),
        foreign_keys=[projet_nsip_referentiel_id],
    )
    referentiel_nsip_activity = db.relationship(
        "Referentiel",
        backref=db.backref("activite_activity", lazy=True),
        foreign_keys=[activite_nsip_referentiel_id],
    )

    # Teams associated with an activity
    teams = db.relationship(
        "Team",
        secondary=activity_teams,
        lazy="subquery",
        backref=db.backref("activity_teams", lazy=True),
    )

    def __repr__(self):
        return f"<Activite(libelle={self.libelle}, id={id})>"


class Projet(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_uuid)
    libelle = db.Column(db.String)
    description = db.Column(db.String)
    ordre = db.Column(db.Integer)

    activite_nsip_referentiel_id = db.Column(db.String, db.ForeignKey("referentiel.id"))
    projet_nsip_referentiel_id = db.Column(db.String, db.ForeignKey("referentiel.id"))

    referentiel_nsip_project = db.relationship(
        "Referentiel",
        backref=db.backref("projet_project", lazy=True),
        foreign_keys=[projet_nsip_referentiel_id],
    )
    referentiel_nsip_activity = db.relationship(
        "Referentiel",
        backref=db.backref("projet_activity", lazy=True),
        foreign_keys=[activite_nsip_referentiel_id],
    )

    # Teams associated with a project
    teams = db.relationship(
        "Team",
        secondary=project_teams,
        lazy="subquery",
        backref=db.backref("project_teams", lazy=True),
    )

    def __repr__(self):
        return f"<Projet(libelle={self.libelle}, id={id})>"


class ActiviteDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activite_id = db.Column(db.String, db.ForeignKey("activite.id"))
    projet_id = db.Column(db.String, db.ForeignKey("projet.id"))
    agent_id = db.Column(db.String, db.ForeignKey("agent.id"))
    team_id = db.Column(db.String, db.ForeignKey("team.id"))
    type = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    pourcent = db.Column(db.Float)
    nbHeures = db.Column(db.Float)

    project = db.relationship("Projet", backref=db.backref("activity_detail", lazy=True))
    agent = db.relationship(
        "Agent",
        backref=db.backref("activity_detail", lazy=True),
        foreign_keys=[agent_id],
    )
    team = db.relationship(
        "Team", backref=db.backref("activity_detail", lazy=True), foreign_keys=[team_id]
    )

    def __repr__(self):
        return (
            f"<ActiviteDetail(id={self.id}, date={self.date}, pourcent={self.pourcent},"
            f" nbHeures={self.nbHeures})>"
        )


class OSITAHSession(db.Model):
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    last_use = db.Column(db.DateTime, nullable=False)


class OSITAHValidation(db.Model):
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    id = db.Column(db.String(36), primary_key=True, default=new_uuid)
    validated = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    initial_timestamp = db.Column(db.DateTime, nullable=True)
    agent_id = db.Column(db.String(36), db.ForeignKey("agent.id"), nullable=False)
    period_id = db.Column(
        db.String(36), db.ForeignKey("ositah_validation_period.id"), nullable=False
    )

    agent = db.relationship("Agent", backref=db.backref("validation", lazy=True))
    period = db.relationship(
        "OSITAHValidationPeriod", backref=db.backref("validation_data", lazy=True)
    )


class OSITAHValidationPeriod(db.Model):
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    id = db.Column(db.String(36), primary_key=True, default=new_uuid)
    name = db.Column(db.String(255), unique=True, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    validation_date = db.Column(db.DateTime, nullable=False)


class OSITAHProjectDeclaration(db.Model):
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    id = db.Column(db.String(36), primary_key=True, default=new_uuid)
    projet = db.Column(db.String(255), nullable=False)
    masterprojet = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    # quotite is the fraction of FTE declared by the agent (1=full time)
    quotite = db.Column(db.Float, nullable=False)
    validation_id = db.Column(db.String(36), db.ForeignKey("ositah_validation.id"), nullable=False)
    # Allow foreign key to Hito projet table to be null so that a Hito project can be delete
    # without deleting the declaration
    hito_project_id = db.Column(db.String(36), db.ForeignKey("projet.id"), nullable=True)

    validation = db.relationship("OSITAHValidation", backref=db.backref("project", lazy=True))
    project = db.relationship("Projet", backref=db.backref("validation_project", lazy=True))
