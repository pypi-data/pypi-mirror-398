## -*- coding: utf-8; -*-
<%inherit file="/master/form.mako" />

<%def name="title()">${index_title} » ${instance_title} » changes @ TXN ${transaction.id}</%def>

<%def name="content_title()">changes @ TXN ${transaction.id}</%def>

<%def name="page_content()">
  <div class="wutta-form-wrapper">

    <b-field label="Changed" horizontal>
      <span>${changed}</span>
    </b-field>

    <b-field label="Changed by" horizontal>
      <span>${transaction.user or ""}</span>
    </b-field>

    <b-field label="IP Address" horizontal>
      <span>${transaction.remote_addr or ""}</span>
    </b-field>

    <b-field label="TXN ID" horizontal>
      <span>${transaction.id}</span>
    </b-field>

    <b-field label="Comment" horizontal>
      <span>${transaction.meta.get("comment", "")}</span>
    </b-field>

  </div>

  <div style="padding: 2rem;">
    % for diff in version_diffs:
        <h4 class="is-size-4 block">${diff.title} (${diff.operation_title})</h4>
        ${diff.render_html()}
    % endfor
  </div>
</%def>
