## -*- coding: utf-8; -*-
<table border="1" style="border-collapse: collapse;">
  <thead>
    <tr>
      % for column in diff.columns:
          <th style="padding: 0.25rem;">${column}</th>
      % endfor
    </tr>
  </thead>
  <tbody>
    % for field in diff.fields:
       ${diff.render_field_row(field)}
    % endfor
  </tbody>
</table>
