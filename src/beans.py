from sys import modules


class PomTraversalException(Exception):
    pass


class Dependency:
    def __init__(self, group_id, artifact_id, version):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

    def __eq__(self, __value):
        return isinstance(__value, self.__class__) and self.group_id == __value.group_id \
            and self.artifact_id == __value.artifact_id \
            and self.version == __value.version

    def __hash__(self):
        return hash((self.group_id, self.artifact_id, self.version))

    def __repr__(self):
        return f"Dependency({self.group_id}:{self.artifact_id}:{self.version})"


class ModulePom:
    def __init__(self, dir_name, pom_path):
        self.dir_name = dir_name
        self.pom_path = pom_path
        # pom general info (name, version, groupId, artifactId)
        self.name = None
        self.info = None

        self.deps = []
        self.props = {}
        self.group2version = {}
        self.parent = None
        self.dep_modules = []

    def find_props(self, prop):
        if prop in self.props:
            return self.props[prop]
        if self.parent is not None:
            return self.parent.find_props(prop)

    def find_group_version(self, group_id):
        if group_id in self.group2version:
            return self.group2version[group_id]
        if self.parent is not None:
            return self.parent.find_group_version(group_id)

    def __repr__(self):
        return f'ModulePom(\'{self.dir_name}\')'


class ApplicationPom:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.modules = []

    def __repr__(self):
        return f'ApplicationPom({self.name})'

    def find_module(self, info: Dependency) -> ModulePom or None:
        if info is None:
            return None
        for x in self.modules:
            if x.info is None:
                continue
            if x.info.artifact_id == info.artifact_id:
                return x
        return None
