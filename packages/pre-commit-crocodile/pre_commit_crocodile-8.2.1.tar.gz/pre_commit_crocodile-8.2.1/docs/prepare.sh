#!/bin/sh

# Configurations
set -e

# Arguments
mode="${1:-}"

# Variables
docs_path=$(cd "$(dirname "${BASH_SOURCE:-${0}}")" && pwd -P)
root_path="${docs_path%/*}"

# Prepare cache
rm -f "${docs_path}/.pages"
rm -f "${docs_path}/commits.generated.md"
rm -f "${docs_path}/index.md"
rm -rf "${docs_path}/about"
rm -f "${docs_path}/assets/stylesheets/variables.scss"

# Cleanup mode
if [ "${mode:-}" = '--clean' ]; then
  return 0
fi

# Configurations
projectAuthor=$(grep '^site_author: ' "${root_path}/mkdocs.yml" | cut -d':' -f2- | xargs echo)
projectCopyright=$(grep '^copyright: ' "${root_path}/mkdocs.yml" | cut -d':' -f2- | xargs echo)
projectDate=$(date '+%d/%m/%Y')
projectKey=$(grep '^sonar\.projectKey=' "${root_path}/sonar-project.properties" | cut -d'=' -f2)
projectName=$(grep '^site_name: ' "${root_path}/mkdocs.yml" | cut -d':' -f2- | xargs echo)
projectNamespace=$(grep '^PROJECT_NAMESPACE = ' "${root_path}/setup.py" | cut -d"'" -f2)
projectPackage=$(grep '^PROJECT_PACKAGE = ' "${root_path}/setup.py" | cut -d"'" -f2)
projectPages=$(grep '^site_url: ' "${root_path}/mkdocs.yml" | cut -d':' -f2- | xargs echo)
projectUrl=$(grep '^repo_url:' "${root_path}/mkdocs.yml" | cut -d':' -f2- | xargs echo)
projectVersion=$(git describe --abbrev=7 --always --long --tags)
projectYear=$(date '+%Y')

# Generate SCSS variables
{
  echo "\$projectAuthor: '${projectAuthor}';"
  echo "\$projectCopyright: '${projectCopyright}';"
  echo "\$projectDate: '${projectDate}';"
  echo "\$projectName: '${projectName}';"
  echo "\$projectVersion: '${projectVersion}';"
  echo "\$projectYear: '${projectYear}';"
} >"${docs_path}/assets/stylesheets/variables.scss"

# Prepare pages
cp -f "${docs_path}/.pages.in" "${docs_path}/.pages"
sed -i "s/%MKDOCS_EXPORTER_PDF_OUTPUT%/${MKDOCS_EXPORTER_PDF_OUTPUT:?}/g" "${docs_path}/.pages"

# Prepare coverage
htmlReportDir=$(grep '^      html_report_dir: ' "${root_path}/mkdocs.yml" | cut -d':' -f2- | xargs echo)
if [ ! -e "${docs_path}/../${htmlReportDir}/index.html" ]; then
  mkdir -p "${docs_path}/../${htmlReportDir}/"
  touch "${docs_path}/../${htmlReportDir}/index.html"
fi

# Export usage
cp -f "${root_path}/README.md" "${docs_path}/index.md"
sed -i "s#\(\[.*\]\)(.*/docs/#\1(#g" "${docs_path}/index.md"

# Export commits
{
  echo '<!-- generated documentation section -->'
  echo ''
  echo '---'
  echo ''
  cz info | sed \
    -e '1{ /^$/d }' \
    -e '/^</,$ { /^</ { s/^/```powershell\n/ }; ${ s/^/```/ } }' \
    -e 's/^\(- \)\{0,1\}\([a-z0-9 ]\{1,\}\): /\1**`\2`:** /g' \
    -e '/^- /s/ \([Bb]uild\|[Bb]ug[s]*\|[Cc]osmetic\|CI\|[Dd]ocumentation\|[Ff]eature[s]*\|[Ff]ixe[s]*\|[Ii]mprove\|[Ii]ssue[s]*\|[Ll]ocal\|[Nn]either\|[Nn]on-production\|[Pp]erformance\|[Ss]ecurity\|[Tt]emporary\|[Tt]est[s]*\)/ **\1**/g' \
    -e 's/\(A scope\|changed file\|modified feature\|within parenthesis\)/**\1**/g' \
    -e 's/\(e.g.\) \([^.]*\)/\1 `\2`/g' \
    -e 's/\(example:\) \([^)]*\)/**\1** `\2`/g' \
    -e "s/\(BREAKING CHANGE[:]*\)/**\`\1\`**/g" \
    -e 's/\(conventional commits\|semantic versioning\)/**\1**/g' \
    -e "s/ '\([A-Za-z0-9:!]\{1,\}\)' / **\`\1\`** /g" \
    -e 's/^\([^#]\{1,\}\)$/\1  /g' \
    -e '/^[^#\[<-]\{1\}[^`]\{1,\}/s/^/\&nbsp;\&nbsp;\&nbsp;\&nbsp; /g' \
    -e '/^### Commit breaking changes$/i <span class="page-break"></span>\n'
  echo ''
  echo '---'
  echo ''
  echo '## Commit example'
  echo ''
  echo '```ruby'
  cz example
  echo '```'
} >"${docs_path}/commits.generated.md"

# Bind 'md_in_html' extension
sed -i \
  -e 's/<\(details\)>/<\1 markdown>/g' \
  -e 's/<\(div style="padding-left: 30px"\)>/<\1 markdown>/g' \
  -e '/<div style="padding-left: 30px"/{ n; /<br/d; }' \
  $(find "${docs_path}/" -name '*.md')

# Inject 'toc' section (PDF only)
find "${docs_path}/" -name '*.md' \
  | while read -r file_path; do
    if ! grep -A1 '^hide:$' "${file_path}" | grep -q '^  - toc$' \
      && ! grep -q '\[TOC\]' "${file_path}" \
      && ! grep -c '^## ' "${file_path}" | grep -q '^0$\|^1$' \
      && ! grep -q '^<!-- documentation no-toc -->$' "${file_path}" \
      && ! grep -q '^<!-- generated documentation section -->$' "${file_path}"; then
      sed -E -i '
        0,/^---$/ {
          s/^---$/---\
\
[TOC]\
\
<span class="page-break"><\/span>/
        }
      ' "${file_path}"
    fi
  done

# Export about/changelog
rm -rf "${docs_path}/about"
mkdir -p "${docs_path}/about/"
if ! type git-cliff >/dev/null 2>&1; then
  alias git-cliff='./.tmp/git-cliff'
fi
{
  echo '---'
  echo 'pdf: false'
  echo '---'
  echo ''
  git-cliff --no-exec --config "${root_path}/config/cliff.toml" \
    | sed '/^- /{ s/</\&lt;/g; s/>/\&gt;/g; }'
} >"${docs_path}/about/changelog.md"
diff -u "${root_path}/CHANGELOG.md" "${docs_path}/about/changelog.md" || true

# Export about/license
{
  echo '---'
  echo 'pdf: false'
  echo '---'
  echo ''
  echo '# License'
  echo ''
  echo '---'
  echo ''
  cat "${root_path}/LICENSE"
} >"${docs_path}/about/license.md"

# Generate about/quality
{
  echo '---'
  echo 'pdf: false'
  echo '---'
  echo ''
  echo '# Quality'
  echo ''
  echo '---'
  echo ''
  echo "## Project"
  echo ''
  echo '<table>'
  echo '  <tbody>'
  echo '    <tr>'
  echo '      <td>'
  echo '        <b>GitLab</b>'
  echo '      </td>'
  echo '      <td>'
  echo "        <a href=\"${projectUrl}/-/releases\">"
  echo "          <img src=\"${projectUrl}/-/badges/release.svg?key_text=release&key_width=60\" alt=\"Release\" style=\"max-width: 100%;\">"
  echo '        </a>'
  echo "        <a href=\"${projectUrl}/-/boards\">"
  echo "          <img src=\"https://img.shields.io/badge/issue-boards-brightgreen?logo=gitlab\" alt=\"Issue boards\" style=\"max-width: 100%;\">"
  echo '        </a>'
  echo "        <a href=\"${projectUrl}/-/packages\">"
  echo "          <img src=\"https://img.shields.io/badge/package-registry-brightgreen?logo=gitlab\" alt=\"Package registry\" style=\"max-width: 100%;\">"
  echo '        </a>'
  echo "        <a href=\"${projectPages}\">"
  echo "          <img src=\"https://img.shields.io/badge/gitlab-pages-brightgreen?logo=gitlab\" alt=\"Pages\" style=\"max-width: 100%;\">"
  echo '        </a>'
  echo '      </td>'
  echo '    </tr>'
  echo '    <tr>'
  echo '      <td>'
  echo '        <b>PyPI</b>'
  echo '      </td>'
  echo '      <td>'
  echo "        <a href=\"https://pypi.org/project/${projectPackage}\">"
  echo "          <img src=\"https://img.shields.io/pypi/v/${projectPackage}?color=blue\" alt=\"Release\" style=\"max-width: 100%;\">"
  echo '        </a>'
  echo "        <a href=\"https://pypi.org/project/${projectPackage}\">"
  echo "          <img src=\"https://img.shields.io/pypi/pyversions/${projectPackage}?color=blue\" alt=\"Python\" style=\"max-width: 100%;\">"
  echo '        </a>'
  echo "        <a href=\"https://pypi.org/project/${projectPackage}\">"
  echo "          <img src=\"https://img.shields.io/pypi/dm/${projectPackage}?color=blue\" alt=\"Downloads\" style=\"max-width: 100%;\">"
  echo '        </a>'
  echo "        <a href=\"${projectUrl}/-/blob/main/LICENSE\">"
  echo "          <img src=\"https://img.shields.io/gitlab/license/${projectNamespace}/${projectName}?color=blue\" alt=\"License\" style=\"max-width: 100%;\">"
  echo '        </a>'
  echo '      </td>'
  echo '    </tr>'
  echo '    <tr>'
  echo '      <td>'
  echo '        <b>SonarCloud</b>'
  echo '      </td>'
  echo '      <td>'
  echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}\">"
  echo "          <img src=\"https://sonarcloud.io/api/project_badges/quality_gate?project=${projectKey}\" alt=\"Quality gate\" style=\"max-width: 100%\">"
  echo '        </a>'
  echo '      </td>'
  echo '    </tr>'
  echo '  </tbody>'
  echo '</table>'
  for branch in 'main' 'develop'; do
    echo ''
    echo '---'
    echo ''
    echo "## Branch ${branch}"
    echo ''
    echo '<table>'
    echo '  <tbody>'
    echo '    <tr>'
    echo '      <td>'
    echo '        <b>GitLab</b>'
    echo '      </td>'
    echo '      <td>'
    echo "        <a href=\"${projectUrl}/-/commits/${branch}/\">"
    echo "          <img src=\"${projectUrl}/badges/${branch}/pipeline.svg\" alt=\"Build\" style=\"max-width: 100%;\">"
    echo '        </a>'
    echo "        <a href=\"${projectUrl}/-/network/${branch}/\">"
    echo "          <img src=\"https://img.shields.io/badge/graph-commits-brightgreen?logo=gitlab\" alt=\"Repository graph\" style=\"max-width: 100%;\">"
    echo '        </a>'
    echo "        <a href=\"${projectUrl}/-/commits/${branch}/\">"
    echo "          <img src=\"https://img.shields.io/badge/repository-commits-brightgreen?logo=gitlab\" alt=\"Repository commits\" style=\"max-width: 100%;\">"
    echo '        </a>'
    echo '      </td>'
    echo '    </tr>'
    echo '    <tr>'
    echo '      <td>'
    echo '        <b>SonarCloud</b>'
    echo '      </td>'
    echo '      <td>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=alert_status\" alt=\"Quality Gate Status\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=bugs&branch=${branch}\" alt=\"Bugs\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=code_smells&branch=${branch}\" alt=\"Code Smells\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=coverage&branch=${branch}\" alt=\"Coverage\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=duplicated_lines_density&branch=${branch}\" alt=\"Duplicated Lines (%)\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=ncloc&branch=${branch}\" alt=\"Lines of Code\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=reliability_rating&branch=${branch}\" alt=\"Reliability Rating\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=security_rating&branch=${branch}\" alt=\"Security Rating\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=sqale_index&branch=${branch}\" alt=\"Technical Debt\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=sqale_rating&branch=${branch}\" alt=\"Maintainability Rating\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo "        <a href=\"https://sonarcloud.io/summary/overall?id=${projectKey}&branch=${branch}\">"
    echo "          <img src=\"https://sonarcloud.io/api/project_badges/measure?project=${projectKey}&metric=vulnerabilities&branch=${branch}\" alt=\"Vulnerabilities\" style=\"max-width: 100%\">"
    echo '        </a>'
    echo '      </td>'
    echo '    </tr>'
    echo '  </tbody>'
    echo '</table>'
  done
} >"${docs_path}/about/quality.md"

# Show documentations
echo ' '
ls -laR "${docs_path}/"
echo ' '
