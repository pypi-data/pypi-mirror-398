## -*- coding: utf-8; -*-
<table class="table is-fullwidth is-bordered is-narrow">
  <thead>
    <tr>
      % for column in diff.columns:
          <th>${column}</th>
      % endfor
    </tr>
  </thead>
  <tbody>
    % for field in diff.fields:
       ${diff.render_field_row(field)}
    % endfor
  </tbody>
</table>
