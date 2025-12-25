Changelog
=========


2.55 (2025-12-22)
-----------------

- Add missing CKEditor style from liege
  [jchandelle]
- Fixed `skin.js` that was not setting correct CSS `top` value for faceted table
  sticky behavior, the faceted table header was no more sticky.
  [gbastien]
- Added some padding top before `Forgot password?` sentence on login form.
  [gbastien]

2.54 (2025-12-01)
-----------------

- Make sure large images do not add horizontal scroll in tooltipsters.
  [gbastien]
- Fixed not used and mismatch use of `evenRowBackgroundColor` and
  `oddRowBackgroundColor`.
  [gbastien]

2.53 (2025-08-21)
-----------------

- URBBDC-3142: Change icon for Housing procedure.
  [aduchene, WBoudabous]


2.52 (2025-06-25)
-----------------

- URBBDC-3142: Add icon for EmptyBuildings procedure.
  [aduchene]
- SUP-44304. Change current state style in urban.
  [jchandelle]
- Fixed edit bar height some times smaller than buttons.
  [gbastien]

2.51 (2025-03-11)
-----------------

- If current URL contains `imio-acceptation`,
  highlight `portal-header` (turn it red).
  [gbastien]

2.50 (2024-09-25)
-----------------

- Fixed faceted dashboard header height to avoid 1px blank space between
  global header and dashboard table header when scrolling
  (sticky dashboard table header).
  [gbastien]

2.49 (2024-06-07)
-----------------

- Use horizontal scroll when tooltipster is too large.
  [gbastien]

2.48 (2024-05-27)
-----------------

- Be more defensive when changing header color to red for test instances
  to avoid elements containing imio-test in id url being wrongly skinned.
  [gbastien]

2.47 (2024-04-10)
-----------------

- URB-3007. Make caduc and abandoned workflow state grey in urban
  [jchandelle]
- Add justice contact icon
  [ndemonte]
- Added style for `concatenate-annexes` batch action button icon.
  [gbastien]
- Avoid `'NoneType' object has no attribute 'get'` in `ImioSearch.filter_query`
  if `query` is `None`.
  [gbastien]

2.46 (2024-03-01)
-----------------

- Added .apButtonAction_download background image.
  [sgeulette]

2.45 (2024-01-02)
-----------------

- Fixed change introduced in release `2.44` with tag `h1` in overlays that
  was impacting other overlays.
  Moreover removed border bottom of `History` title in history overlay.
  [gbastien]

2.44 (2023-11-27)
-----------------

- Now that element's title (pretty link) is displayed in `@@historyview`,
  display `h1` in overlay the same size it is display out of an overlay.
  [gbastien]

2.43 (2023-08-24)
-----------------

- Fix document generation actions on dashboard for urban [URB-2863]
  [mpeeters]
- Fix faceted autocomplete widget width in urban [URB-2866]
  [jchandelle]
- Removed styling rule for `.tooltipster-base img` as image `height/width`
  is now forced to `16px` in `collective.iconifiedcategory`.
  [gbastien]

2.42 (2023-07-07)
-----------------

- `get_state_infos` was moved from `imio.helpers.content` to
  `imio.helpers.workflow`, adapted import accordingly.
  [gbastien]

2.41 (2023-06-27)
-----------------

- Style table header the same way for HTML tables and DX/AT datagrid fields.
  [gbastien]

2.40 (2023-06-15)
-----------------

- Add a red color to the denied status of divisions
  [fngaha]

2.39 (2023-03-29)
-----------------

- Fixed css to align multi select2 widget to the left.
  [sgeulette]

2.38 (2023-02-13)
-----------------

- Added `.no-style-table tr.hide-bottom-border` that will remove
  the bottom border when displaying fields in a table.
  [gbastien]
- Avoid large image breaking the advice tooltipster.
  [gbastien]
- Style results displayed in `referencebrowserwidget`.
  [gbastien]
- Adapted override of `collective.messagesviewet` viewlet manager as base class
  and definition were changed since integration of global/local messages.
  [gbastien]
- Make `ftw.labels` configuration label edit overlay larger.
  [gbastien]

2.37 (2022-08-26)
-----------------

- CSS for `generationlinks` from `collective.documentgenerator` now that templates
  are grouped by title, the title is no more clickable so make the icon larger,
  make the icons look like buttons.
  [gbastien]
- On hover of `prettylink` in `#portal-column-one`, apply same styles as in `#content`.
  [gbastien]
- Removed rule `vertical-align: bottom;` for `#content input`.
  [gbastien]
- Fixed contenttype icon `max-width` to 16px, necessary when the img is a svg.
  [gbastien]

2.36 (2022-06-17)
-----------------

- Do not force an height for img or it hides broken images.
  [gbastien]

2.35 (2022-05-17)
-----------------

- Completed CSS for `livesearch`, make it looks correctly in Chrome too.
  [gbastien]

2.34 (2022-05-16)
-----------------

- Fixed the default Plone `@@search`:

  - Hide the wildcard search madness, do not display a `*`, every searches are
    done wildcard like it is the case in dashboards;
  - Only display link to `Advanced search` in the livesearch response,
    hide the `Show all results`.

  [gbastien]

2.33 (2022-04-26)
-----------------

- Added some margin at right of a tooltipster so it is never sticked to the screen edge.
  [gbastien]
- Make sure very long words are splitted, this is necessary for Firefox where
  a very long word (or a sentence made of words separated by `-` withtout `blank`)
  was not splitted, making a long horizontal scroll appear.
  [gbastien]

2.32 (2022-03-22)
-----------------

- Fix, add margin under a `tooltipster` only if it is not displayed `top`
  or there is space between tooltipster and origin.
  [gbastien]

2.31 (2022-03-22)
-----------------

- Added some margin under a tooltipster so it is never sticked to the screen edge.
  [gbastien]

2.30 (2022-03-07)
-----------------

- If current URL contains `preprod`, highlight `portal-header` (turn it red).
  [jjaumotte]
- Reduce size of `h1 title`, in view mode as well as in edit mode (input).
  [gbastien]

2.29 (2021-11-08)
-----------------

- Make abbr/acronym tag display better (space between text and dotted border).
  [gbastien]

2.28 (2021-10-13)
-----------------

- Set size of svg content icon in `folder_factories`.
  [gbastien]

2.27 (2021-08-27)
-----------------

- Added some space between input of an AT multiselection widget.
  [gbastien]
- Added borders on fieldset tabs to distinguish them clearlier.
  [sgeulette]
- Removed icons used to manage "More/Less filters" on the faceted search,
  replace it with an "Advanced search" link and a "Search" icon.
  We rely on collective.fontawesome for the "Search" icon.
  [gbastien]
- Removed styles about `enableFormTabbing` displayed on view, this interacts
  when editing an element in an overlay (because parent frame is a view)
  and does not seem used anywhere?
  [gbastien]

2.26 (2021-07-16)
-----------------

- imioapps : avoid empty blank space at bottom of tooltipster by using
  `height:auto` on tooltispter container.
  [gbastien]

2.25 (2021-07-16)
-----------------

- imioapps : harmonize input border color with `select2` input (a bit darker).
  [gbastien]
- plonemeetingskin : remove defined height for `viewlet-below-content-title`.
  [gbastien]
- imioapps : added delete icon on delete batch action button and
  download icon on download annexes batch action button.
  [gbastien]
- Limit `select_row` column with as much as possible.
  [gbastien]
- imioapps : increased a bit padding bottom between fields on edit forms.
  [gbastien]

2.24 (2021-04-21)
-----------------

- Fixed problems with too high `tooltipster` overflowing the screen,
  fixed a `max-height` so we have a vertical scroll when necessary.
  [gbastien]
- Changed ia.docs footer viewlets
  [sgeulette]

2.23 (2021-03-12)
-----------------

- Display `cursor: pointer;` when hovering a button or a checkbox.
  [gbastien]
- Resized svg documentgenerator icons
  [sgeulette]
- Avoid tooltipster of more than 80% width.
  [gbastien]
- Move urban css and icons to plonetheme.imioapps.
  [sdelcourt]

2.22 (2021-01-06)
-----------------

- imioapps : use `width:auto` for overlay popups and set `max-height: 800px`
  to avoid vertical scroll as much as possible.
  [gbastien]
- imioapps : fix `referencebrowserwidget` batching hover and search button size.
  [gbastien]
- imioapps : make the `hover` on pretty links work again.
  [gbastien]
- imioapps : specifically do not add bottom border on `<tr>` of `<table>` using
  `no-style-table` when class `no-border` is applied on `<tr>` tag.
  [gbastien]
- imioapps : in styles defined to avoid using Firefox default (see version 2.19),
  set a lighter border for input/textarea/...
  [gbastien]
- imioapps : make sure the ajax spinner is displayed hover overlays.
  [gbastien]
- imioapps : make the checkboxes displayed in dashboard `CheckBoxColumn`
  column easier to click.
  [gbastien]
- imioapps : add a specific CSS class on body using JS function when brower is
  using `Chrome/Chromium/Safari` (`using-chrome`) or
  when it is using `Firefox` (`using-firefox`).
  [gbastien]
- imioapps : make the faceted result table header sticky.
  [gbastien]

2.21 (2020-10-07)
-----------------

- imioapps : skin data displayed in `PrettyLinkWithAdditionalInfosColumn` column,
  add some margin between data.
  [gbastien]

2.20 (2020-09-07)
-----------------

- plonemeetingskin : increase base line-height as font-size was increased.
  [gbastien]

2.19 (2020-09-01)
-----------------

- Fix input text/passowrd and textarea background-color so default styles
  applied by Firefox are overrided (Firefox 80+).
  [gbastien]

2.18 (2020-08-18)
-----------------

- imioapps : style the `PloneGroupUsersGroupsColumn` column.
  [gbastien]
- plonemeetingskin : make sure very large images are not
  exceeding the screen.
  [gbastien]
- plonemeetingskin : removed useless styles about `actionMenuAX`
  that was replaced by `tooltipster`.
  [gbastien]
- imioapps : make sure input submit/button use `cursor:pointer`, moreover
  fix Firefox disappearance of `outline` when an `input submit` is clicked,
  replace it with a `box-shadow` as we use `border-radius`.
  [gbastien]
- imioapps : remove multiple definition for `#content legend padding`.
  [gbastien]

2.17 (2020-06-24)
-----------------

- plonemeetingskin : moved rules with logic to hide something
  back to plonemeting.css
  [gbastien]
- Make sure tooltipster tooltip arrow is displayed correctly
  (stay sticked to the tooltipster) when zooming in the internet browser.
  [gbastien]

2.16 (2020-04-02)
-----------------

- Added configurable help icon on the site header
  [sdelcourt]
- More precise CSS selector to hide CKEditor's spellchecking ad.
  [gbastien]

2.15 (2020-03-12)
-----------------

- Avoid too much padding top and left in CKeditor edit zone.
  [gbastien]
- Added a new CSS rule to hide CKEditor's spellchecking ad [aduchene]

2.14 (2020-02-06)
-----------------

- plonemeetingskin : added icon for 'wait advices' WF action panel button.
  [gbastien]

2.13 (2020-01-10)
-----------------

- As state color is defined on `<span>` with `imio.prettylink`,
  define `linkColor` on hover.
  [gbastien]

2.12 (2019-10-14)
-----------------

- Use common CSS for workflowstate viewlet.
  [gbastien]

2.11 (2019-09-12)
-----------------

- Added style for apButtonSelect class of actionspanel.
  [sgeulette]
- Added CSS for datagridfield rendered in a dashboard additional infos column.
  [gbastien]
- Added workflowstate viewlet
  [sgeulette]
- Added css for apButtonAction_edit.
  [sgeulette]

2.10 (2019-06-28)
-----------------

- Set `collective.behavior.talcondition` input field `width` to `99%`.
  [gbastien]

2.9 (2019-06-08)
----------------

- Set `padding-top: 0.5em;` instead `padding-top: 1em;` for
  `td.table_widget_value` so it is the same value as for
  `td.table_widget_label` and label/value are correctly aligned in views
  using it (our default dexterity view).
  [gbastien]

2.8 (2019-05-16)
----------------

- Added spinner_small.gif image and use it in the async_actions_panel div.
  [gbastien]
- Purge and redefine bundles used by resources registries
  (portal_css/portal_javascripts).
  [gbastien]
- Make sure a:visited links in portlets have same color as a:link.
  [gbastien]
- As header's height is `position:fixed`, compute the `#emptyviewlet`'s height
  dynamically using JS.  Viewlet's height is computed by calling the JS method
  directly in `empty.pt` so we do not see viewlet size changing.
  [gbastien]
- If current URL contains `imio-test`, highlight `portal-header` (turn it red).
  [gbastien]
- Override the `plone_context_state` view to redefine `canonical_object_url`
  to strip the `URL` containing `portal_factory` as this URL is used to call
  asynchronous JS functions.
  [gbastien]

2.7 (2019-01-28)
----------------

- pst css.
  [sgeulette]

2.6 (2019-01-25)
----------------

- imioapps : fixed fieldset legend height to 18px.
  [gbastien]
- plonemeetingskin : added icon for 'reorder items' action panel button.
  [gbastien]

2.5 (2018-12-18)
----------------

- imioapps : limit margin-bottom under fieldset.
  [gbastien]
- plonemeetingskin : remove margin under table displaying item infos
  on the item view.
  [gbastien]

2.4 (2018-12-04)
----------------

- plonemeetingskin : do not define border for .enableFormTabbing on
  faceted navigation.
  [gbastien]

2.3 (2018-11-29)
----------------

- Make sure dotted bottom border is displayed when using class 'link-tooltip'
  and element is used in a table.listing because base.css removes border-bottom
  using a !important...
  [gbastien]

2.2 (2018-11-20)
----------------

- Do not use `"` in dtml `fontFamily` property from `imioapps_properties.props`
  or it can not be used in `dtml`, used `'` instead.
  [gbastien]
- Skin `Add contact` link at bottom of `collective.contact.core` organization
  view so it is isolated from linked contacts and displayed correctly when
  using an actions panel viewlet at the bottom of the page.
  [gbastien]
- Set relative position on header in manage-viewlets view
  [sgeulette]
- Skin `collective.contact.core` `tooltip` to manage fixed width and correct
  display when `tooltip` content is too long.
  [gbastien]
- Skin z3c.form datagridfield to indentify row content.
  [gbastien]
- Added css to style as list li tag in overlay link integrity delete confirmation
  [sgeulette]
- Increase height of dropdown list of querystring dropdown widget
  (Collection query field widget).
  [gbastien]
- Be more precise about label for which bold is removed, only apply to
  multiselection lists of DX and AT.
  [gbastien]
- Adapted to not use position:absolute for fieldset legend.
  [gbastien]

2.1 (2018-07-23)
----------------

- Fix header so it is always visible.
  [gbastien]
- Depends on `collective.messagesviewlet` as we override the viewlet to move it
  from `IPortalHeader` to `IPortalTop` viewletmanager.
  [gbastien]
- Updated spinner.gif image to fit with skin default colors.
  [gbastien]
- Removed left-padding for #portal-globalnav.
  [gbastien]

2.0.17 (2018-04-20)
-------------------

- Limit padding for tooltipstered content.
  [gbastien]

2.0.16 (2018-02-23)
-------------------

- Adapted to new styles of tooltipster 4.2.6.
  [gbastien]

2.0.15 (2018-01-30)
-------------------

- Skin column-two the same way as column-one.  This makes portlets displayed
  on the left or on the right look similar.
  [gbastien]
- Hide borders of tables using class `no-style-table`.
  [gbastien]

2.0.14 (2017-12-07)
-------------------

- Only display the `scan` tab on annexes to roles `Manager/MeetingManager`.
  [gbastien]

2.0.13 (2017-11-28)
-------------------

- Set `vertical-align: bottom` for `input` instead `vertical-align: text-top`
  for `label` to align `input` and `label` correctly.
  [gbastien]

2.0.12 (2017-11-24)
-------------------

- Added favicon.
  [sgeulette]
- Skin `input#form-buttons-cancel` the same way `input.standalone` and skin
  `collective.eeafaceted.batchactions` buttons the same way `imio.actionspanel`
  buttons.
  [gbastien]

2.0.11 (2017-10-05)
-------------------

- Display navigation portlet same way as other portlets.
  [gbastien]
- Display the infos in the CKeditor SCAYT WebSpellChecker popup correctly.
  [gbastien]

2.0.10 (2017-08-30)
-------------------

- Removed styling for class `form.apFormButton` as it was removed from
  imio.actionspanel 1.29+, the add content select now uses the standard
  `apButton` CSS class like other buttons.
  [gbastien]
- Skin portletFooter to align it right.
  [gbastien]

2.0.9 (2017-08-28)
------------------

- Added icon for the store_every_items_decision_as_annex action
  in the plonemeetingskin.
  [gbastien]
- Fixed fieldset/legend top padding.

2.0.8 (2017-06-09)
------------------

- Make <abbr> and <acronym> dotted underline work for every browsers.
  [gbastien]
- Removed useless code about MeetingFile in plonemeetingskin.
  [gbastien]
- Display <th> of table the same way as it is rendered by appy.pod, namely text
  black and grey background.
  [gbastien]

2.0.7 (2017-03-22)
------------------

- Use a brighter blue color for links.
  [gbastien]

2.0.6 (2017-03-14)
------------------

- Highlight the 'lost password?' link in the login_form.
- Style actionspanel select button
- Adapted styles so font-size and line-height are the same while using CKeditor
- Added file imioapps_ckeditor_moonolisa.css.dtml that is enabled when the
  Moono-Lisa skin is selected in CKEditor properties.  This makes it work
  correctly in Chrome and greyed a bit more the selected buttons
- Reduce fieldset padding in form fieldset tabbing

2.0.5 (2017-01-25)
------------------

- Do not use 'float: left;' to move the <legend> tag, it is not working
  anymore with recent versions of Chrome.  Instead use 'position: absolute;'.
  This works in both FF and Chrome and simplify overal CSS.
- Display AT and DX field title bold but selectable contents as normal.
  This is the case for radio buttons, multiple checkboxes, ...

2.0.4 (2016-12-05)
------------------

- Added margin-left for listingBar 'next elements' button or it sticks
  to previous one. This appears until Plone 4.3.8.
- Update pstskin profile (reduce logo, change css)


2.0.3 (2016-06-17)
------------------

- Removed styling for tags <acronym> and <abbr>.
- Optimized icon position on buttons.
- Small fixes for Chrome.


2.0.2 (2016-05-17)
------------------

- Display header correctly for anonymous when portal_tabs are displayed.
- Removed padding-left added by Firefox to input.
- Skin portlet News.


2.0.1 (2016-05-13)
------------------

- Use navBackgroundColor for listingBar hover and select color.
- Make sure broken images are shown in FF.
- Display default faceted widgets (not advanced) the same height.


2.0 (2016-04-19)
----------------

- New layout.


1.2.7 (2016-01-21)
------------------

- Removed 'meetingadvice' icon relevant CSS as it uses a real icon now.
- Define 'height' for search button so it is displayed correctly in Chrome.
- Added left/right padding to collective.messagesviewlet message.
- Limit padding in z3ctable header cells.


1.2.6 (2015-12-03)
------------------

- imioapps : use a bigger spinner.gif and grey page when faceted is locked

1.2.5 (2015-07-14)
------------------

- Several adaptations regarding imio.dashboard integration

1.2.4 (2015-03-18)
------------------
- plonemeetingskin : do not display a contenttype-x icon for type 'MeetingFile' and 'MeetingItem'
- imioapps : skin also listingBar displayed in referencebrowserwidget

1.2.3 (2014-09-23)
------------------
- Added back skins.zcml that register File System Directory Views
- Added profile to go to version 1.2.3 that removes old _templates File System Directory Views

1.2.2 (2014-09-23)
------------------
- Fixes.

1.2.1 (2014-09-23)
------------------
- Fixes.

1.2 (2014-09-22)
----------------
- Fixes.

1.1 (2014-03-07)
----------------
- Adapted styles

1.0 (2014-02-12)
----------------
- First release, added 4 skins : dmsmailskin, imioapps, plonemeetingskin, pstskin
