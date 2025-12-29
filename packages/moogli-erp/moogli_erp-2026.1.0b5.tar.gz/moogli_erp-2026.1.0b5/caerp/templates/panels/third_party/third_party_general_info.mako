<%namespace file="/base/utils.mako" import="format_mail" />
<%namespace file="/base/utils.mako" import="format_phone" />
<%namespace file="/base/utils.mako" import="format_text" />

<div class="layout flex content_vertical_padding">
    % if third_party.is_company():
        <span class="user_avatar">${api.icon('building')}</span>
        <div>
            <h3>
                ${third_party.label}
                % if third_party.label != third_party.company_name:
                    <small>( ${third_party.company_name} )</small>
                % endif
            </h3>
            <small><em>Personne morale</em></small>
        </div>
    % elif third_party.is_internal():
        <span class="user_avatar">${api.icon('house')}</span>
        <div>
            <h3>${third_party.label}</h3>
            <small><em>Enseigne interne à la CAE</em></small>
        </div>
    % else:
        <span class="user_avatar">${api.icon('user')}</span>
        <div>
            <h3>${third_party.label}</h3>
            <small><em>Personne physique</em></small>
        </div>
    % endif
</div>
<div class="data_display content_vertical_padding">
    <div>
        % if third_party.is_company() and third_party.get_contact_label():
            <dl>
                <div>
                    <dt>Contact principal</dt>
                    <dd>${third_party.get_contact_label()}</dd>
                </div>
                % if third_party.function:
                    <div>
                        <dt>Fonction</dt>
                        <dd>${format_text(third_party.function)}</dd>
                    </div>
                % endif
            </dl>
            <br/><br/>
        % endif
        ${format_text(third_party.full_address)}
    </div>
    <div>
        <dl class="data_number">
            % if third_party.is_company():
                <div>
                    <dt>Numéro d’identification</dt>
                    <dd>
                        % if third_party.get_company_identification_number():
                            ${third_party.get_company_identification_number()}
                        % else:
                            <em>Non renseigné</em>
                        % endif
                    </dd>
                </div>
                <div>
                    <dt>TVA intracommunautaire</dt>
                    <dd>
                        % if third_party.tva_intracomm:
                            ${third_party.tva_intracomm}
                        % else:
                            <em>Non renseigné</em>
                        % endif
                    </dd>
                </div>
            % endif
        </dl>
        <dl>
            <div>
                <dt>Adresse électronique</dt>
                <dd>
                    % if third_party.email:
                        ${format_mail(third_party.email)}
                    % else:
                        <em>Non renseigné</em>
                    % endif
                </dd>
            </div>
            <div>
                <dt>Téléphone portable</dt>
                <dd>
                    % if third_party.mobile:
                        ${format_phone(third_party.mobile, 'mobile')}
                    % else:
                        <em>Non renseigné</em>
                    % endif
                </dd>
            </div>
            <div>
                <dt>Téléphone</dt>
                <dd>
                    % if third_party.phone:
                        ${format_phone(third_party.phone, 'desk')}
                    % else:
                        <em>Non renseigné</em>
                    % endif
                </dd>
            </div>
        </dl>
    </div>

</div>
