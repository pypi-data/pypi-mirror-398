<div class="dash_elem highlight">
    <h2>
        <span class='icon caution'>${api.icon('newspaper')}</span>
        <a href="/release_notes?version_es" title="Voir l'ensemble des notes de version">
            <span>Nouveautés de la dernière version</span>
            ${api.icon('arrow-right')}
        </a>
    </h2>
    <div class='panel-body'>
        % if last_version_resume_es:
            <ul>
                % for resume in last_version_resume_es:
                    <li><span class="icon">${api.icon("star")}</span> ${resume}</li>
                % endfor
                <li><a href="/release_notes?version_es">Voir toutes les nouveautés</a></li>
            </ul>
        % else:
            <p><em>Aucune nouveauté mise en avant</em></p>
        % endif
    </div>
</div>
