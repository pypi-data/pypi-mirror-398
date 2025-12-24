## -*- coding: utf-8; -*-
<%inherit file="/page.mako" />

<%def name="title()">${index_title} » ${instance_title} » history</%def>

<%def name="content_title()">Version History</%def>

<%def name="page_content()">
  ${grid.render_vue_tag()}
</%def>

<%def name="render_vue_templates()">
  ${parent.render_vue_templates()}
  ${grid.render_vue_template()}
</%def>

<%def name="make_vue_components()">
  ${parent.make_vue_components()}
  ${grid.render_vue_finalize()}
</%def>
