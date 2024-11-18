import os.path
import xml.etree.ElementTree as ET

from src.beans import Dependency, ApplicationPom, ModulePom

MAVEN_NAMESPACE = 'http://maven.apache.org/POM/4.0.0'
NAMESPACES = {'m': MAVEN_NAMESPACE}


class PomParser:

    def __init__(self, app: ApplicationPom):
        self.app = app
        self.pom_path2module = {}
        for it in app.modules:
            self.pom_path2module[it.pom_path] = it

    def parse(self):
        # self.__parse_module(self.app.root_module)
        print(f"Parsing {self.app}")
        for module in self.app.modules:
            tree = ET.parse(module.pom_path)
            root = tree.getroot()

            self.__enrich_properties(module, root)
            self.__enrich_parent(module, root)

            self.__enrich_basic(module, root)
            self.__enrich_dependencies(module, root)

        for module in self.app.modules:
            self.parse_unresolved_deps(module)

        print(f"Finish parsing {self.app}")

    def __enrich_dependencies(self, module: ModulePom, root_el):
        for dep in root_el.findall(".//m:dependencies/m:dependency", NAMESPACES):
            dep = self.__get_dep(dep)
            module.deps.append(dep)
            self.define_version(module, dep)

        module.deps.sort(key=lambda d: (d.group_id, d.artifact_id))

    def define_version(self, module, dep):
        if dep.version.startswith('${'):
            tag_version = dep.version[2:-1].strip()
            version = module.find_props(tag_version)
            if version == "" or version is None:
                print(
                    f"Couldn't find version for tag {tag_version} in props of {dep.group_id}.{dep.artifact_id} in module {module}")
            else:
                dep.version = version
            module.group2version[dep.group_id] = dep.version
        elif dep.version == "" or dep.version is None:
            dep.version = module.find_group_version(dep.group_id)
        else:
            module.group2version[dep.group_id] = dep.version.strip()

    def __enrich_basic(self, module: ModulePom, root_el):
        dep = self.__get_dep(root_el)
        self.define_version(module, dep)
        module.info = dep
        name = root_el.find("m:name", NAMESPACES)
        module.name = name.text if name is not None else ""

    def __enrich_parent(self, module: ModulePom, root_el):
        parent = root_el.find(".//m:parent", NAMESPACES)
        if parent is None:
            return
        relative_path = parent.find("m:relativePath", NAMESPACES)
        if relative_path is not None and relative_path.text is not None:
            full_rel_path = os.path.abspath(os.path.join(os.path.dirname(module.pom_path), relative_path.text))
            if full_rel_path in self.pom_path2module:
                parent_module = self.pom_path2module[full_rel_path]
                module.parent = parent_module

                parent_module.dep_modules.append(module)
            else:
                print(f"Can't find parent for module {module}")
        else:
            dep = self.__get_dep(parent)
            self.define_version(module, dep)
            module.deps.append(dep)
            module.parent = self.app.find_module(dep)

            if module.parent is None:
                print(f"Can't find parent for module {module}")
            else:
                module.parent.dep_modules.append(module)

    def __get_dep(self, root_el):
        group_id = root_el.find("m:groupId", NAMESPACES)
        group_id = group_id.text if group_id is not None else ""
        artifact_id = root_el.find("m:artifactId", NAMESPACES)
        artifact_id = artifact_id.text if artifact_id is not None else ""
        version = root_el.find("m:version", NAMESPACES)
        version = version.text if version is not None else ""
        return Dependency(group_id, artifact_id, version)

    def __enrich_properties(self, module: ModulePom, root_el):
        properties = root_el.find(".//m:properties", NAMESPACES)
        if properties is not None:
            for prop in properties:
                prop_tag = prop.tag[len(MAVEN_NAMESPACE) + 2:]
                module.props[prop_tag] = prop.text.strip()
                if prop_tag == 'java.version':
                    module.deps.append(Dependency('', 'Java', prop.text.strip()))

    def parse_unresolved_deps(self, module: ModulePom):
        for dep in module.deps:
            if dep.version == "" or dep.version is None:
                dep.version = module.find_group_version(dep.group_id)
                if dep.version == "" or dep.version is None:
                    selected_version, max_points, selected_group_id = self.__get_similarity_score_group_id(dep.group_id,
                                                                                                           module)
                    if max_points >= len(dep.group_id.split('.')) - 1:
                        dep.version = selected_version
                        print(
                            f'Set similar group version for {dep.group_id} to {selected_version} in group {selected_group_id}')
                    else:
                        dep.version = 'NotFound'
                        print(f'Unable to define version of {dep} in {module}')

    def __get_similarity_score_group_id(self, group_left, module):
        selected_version = None
        selected_group_id = None
        max_points = 0
        for group_id, version in module.group2version.items():
            points = self.__get_group_equality_points(group_left, group_id)
            if max_points < points:
                max_points = points
                selected_group_id = group_id
                selected_version = version
        if module.parent is not None:
            s_version, m_points, s_group_id = self.__get_similarity_score_group_id(group_left, module.parent)
            if m_points > max_points:
                max_points = m_points
                selected_version = s_version
                selected_group_id = s_group_id

        return selected_version, max_points, selected_group_id

    def __get_group_equality_points(self, group_left, group_right):
        if group_left == group_right:
            return True
        if group_left is None or group_right is None:
            return False
        left_split = group_left.split('.')
        right_split = group_right.split('.')
        max_cnt = 0
        for it in range(min(len(left_split), len(right_split))):
            if left_split[it] == right_split[it]:
                max_cnt += 1
        return max_cnt

# __parse_pom('waw', {'wa':2})
