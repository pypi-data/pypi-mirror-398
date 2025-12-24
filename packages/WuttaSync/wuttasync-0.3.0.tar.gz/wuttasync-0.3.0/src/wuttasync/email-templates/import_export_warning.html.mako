## -*- coding: utf-8; -*-
<html>
  <body>
    <h3>Diff warning for ${title} (${handler.actioning})</h3>

    <p style="font-style: italic;">
      % if dry_run:
          <span style="font-weight: bold;">DRY RUN</span>
          - these changes have not yet happened
      % else:
          <span style="font-weight: bold;">LIVE RUN</span>
          - these changes already happened
      % endif
    </p>

    <ul>
      % for model, (created, updated, deleted) in changes.items():
          <li>
            <a href="#${model}">${model}</a> -
            ${app.render_quantity(len(created))} created;
            ${app.render_quantity(len(updated))} updated;
            ${app.render_quantity(len(deleted))} deleted
          </li>
      % endfor
    </ul>

    <p>
      <span style="font-weight: bold;">COMMAND:</span>
      &nbsp;
      <code>${argv}</code>
    </p>

    <p>
      <span style="font-weight: bold;">RUNTIME:</span>
      &nbsp;
      ${runtime} (${runtime_display})
    </p>

    % for model, (created, updated, deleted) in changes.items():

        <br />
        <h4>
          <a name="${model}">${model}</a> -
          ${app.render_quantity(len(created))} created;
          ${app.render_quantity(len(updated))} updated;
          ${app.render_quantity(len(deleted))} deleted
        </h4>

        <div style="padding-left: 2rem;">

          % for obj, source_data in created[:max_diffs]:
              <h5>${model} <em>created</em> in ${target_title}: ${obj}</h5>
              <% diff = make_diff({}, source_data, nature="create") %>
              <div style="padding-left: 2rem;">
                ${diff.render_html()}
              </div>
          % endfor
          % if len(created) > max_diffs:
              <h5>${model} - ${app.render_quantity(len(created) - max_diffs)} more records <em>created</em> in ${target_title} - not shown here</h5>
          % endif

          % for obj, source_data, target_data in updated[:max_diffs]:
              <h5>${model} <em>updated</em> in ${target_title}: ${obj}</h5>
              <% diff = make_diff(target_data, source_data, nature="update") %>
              <div style="padding-left: 2rem;">
                ${diff.render_html()}
              </div>
          % endfor
          % if len(updated) > max_diffs:
              <h5>${model} - ${app.render_quantity(len(updated) - max_diffs)} more records <em>updated</em> in ${target_title} - not shown here</h5>
          % endif

          % for obj, target_data in deleted[:max_diffs]:
              <h5>${model} <em>deleted</em> in ${target_title}: ${obj}</h5>
              <% diff = make_diff(target_data, {}, nature="delete") %>
              <div style="padding-left: 2rem;">
                ${diff.render_html()}
              </div>
          % endfor
          % if len(deleted) > max_diffs:
              <h5>${model} - ${app.render_quantity(len(deleted) - max_diffs)} more records <em>deleted</em> in ${target_title} - not shown here</h5>
          % endif

        </div>

    % endfor
  </body>
</html>
