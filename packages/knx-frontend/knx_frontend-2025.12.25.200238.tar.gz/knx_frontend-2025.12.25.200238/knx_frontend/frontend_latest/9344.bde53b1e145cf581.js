/*! For license information please see 9344.bde53b1e145cf581.js.LICENSE.txt */
export const __webpack_id__="9344";export const __webpack_ids__=["9344"];export const __webpack_modules__={87400:function(t,e,a){a.d(e,{l:()=>i});const i=(t,e,a,i,s)=>{const r=e[t.entity_id];return r?o(r,e,a,i,s):{entity:null,device:null,area:null,floor:null}},o=(t,e,a,i,o)=>{const s=e[t.entity_id],r=t?.device_id,n=r?a[r]:void 0,l=t?.area_id||n?.area_id,c=l?i[l]:void 0,d=c?.floor_id;return{entity:s,device:n||null,area:c||null,floor:(d?o[d]:void 0)||null}}},31747:function(t,e,a){a.a(t,(async function(t,i){try{a.d(e,{T:()=>n});var o=a(22),s=a(22786),r=t([o]);o=(r.then?(await r)():r)[0];const n=(t,e)=>{try{return l(e)?.of(t)??t}catch{return t}},l=(0,s.A)((t=>new Intl.DisplayNames(t.language,{type:"language",fallback:"code"})));i()}catch(n){i(n)}}))},72125:function(t,e,a){a.d(e,{F:()=>o,r:()=>s});const i=/{%|{{/,o=t=>i.test(t),s=t=>{if(!t)return!1;if("string"==typeof t)return o(t);if("object"==typeof t){return(Array.isArray(t)?t:Object.values(t)).some((t=>t&&s(t)))}return!1}},56528:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),o=a(96196),s=a(77845),r=a(92542),n=a(55124),l=a(31747),c=a(45369),d=(a(56565),a(69869),t([l]));l=(d.then?(await d)():d)[0];const h="preferred",p="last_used";class u extends o.WF{get _default(){return this.includeLastUsed?p:h}render(){if(!this._pipelines)return o.s6;const t=this.value??this._default;return o.qy`
      <ha-select
        .label=${this.label||this.hass.localize("ui.components.pipeline-picker.pipeline")}
        .value=${t}
        .required=${this.required}
        .disabled=${this.disabled}
        @selected=${this._changed}
        @closed=${n.d}
        fixedMenuPosition
        naturalMenuWidth
      >
        ${this.includeLastUsed?o.qy`
              <ha-list-item .value=${p}>
                ${this.hass.localize("ui.components.pipeline-picker.last_used")}
              </ha-list-item>
            `:null}
        <ha-list-item .value=${h}>
          ${this.hass.localize("ui.components.pipeline-picker.preferred",{preferred:this._pipelines.find((t=>t.id===this._preferredPipeline))?.name})}
        </ha-list-item>
        ${this._pipelines.map((t=>o.qy`<ha-list-item .value=${t.id}>
              ${t.name}
              (${(0,l.T)(t.language,this.hass.locale)})
            </ha-list-item>`))}
      </ha-select>
    `}firstUpdated(t){super.firstUpdated(t),(0,c.nx)(this.hass).then((t=>{this._pipelines=t.pipelines,this._preferredPipeline=t.preferred_pipeline}))}_changed(t){const e=t.target;!this.hass||""===e.value||e.value===this.value||void 0===this.value&&e.value===this._default||(this.value=e.value===this._default?void 0:e.value,(0,r.r)(this,"value-changed",{value:this.value}))}constructor(...t){super(...t),this.disabled=!1,this.required=!1,this.includeLastUsed=!1,this._preferredPipeline=null}}u.styles=o.AH`
    ha-select {
      width: 100%;
    }
  `,(0,i.__decorate)([(0,s.MZ)()],u.prototype,"value",void 0),(0,i.__decorate)([(0,s.MZ)()],u.prototype,"label",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean,reflect:!0})],u.prototype,"disabled",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"required",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],u.prototype,"includeLastUsed",void 0),(0,i.__decorate)([(0,s.wk)()],u.prototype,"_pipelines",void 0),(0,i.__decorate)([(0,s.wk)()],u.prototype,"_preferredPipeline",void 0),u=(0,i.__decorate)([(0,s.EM)("ha-assist-pipeline-picker")],u),e()}catch(h){e(h)}}))},2076:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),o=a(96196),s=a(77845),r=(a(60961),a(88422)),n=t([r]);r=(n.then?(await n)():n)[0];const l="M15.07,11.25L14.17,12.17C13.45,12.89 13,13.5 13,15H11V14.5C11,13.39 11.45,12.39 12.17,11.67L13.41,10.41C13.78,10.05 14,9.55 14,9C14,7.89 13.1,7 12,7A2,2 0 0,0 10,9H8A4,4 0 0,1 12,5A4,4 0 0,1 16,9C16,9.88 15.64,10.67 15.07,11.25M13,19H11V17H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12C22,6.47 17.5,2 12,2Z";class c extends o.WF{render(){return o.qy`
      <ha-svg-icon id="svg-icon" .path=${l}></ha-svg-icon>
      <ha-tooltip for="svg-icon" .placement=${this.position}>
        ${this.label}
      </ha-tooltip>
    `}constructor(...t){super(...t),this.position="top"}}c.styles=o.AH`
    ha-svg-icon {
      --mdc-icon-size: var(--ha-help-tooltip-size, 14px);
      color: var(--ha-help-tooltip-color, var(--disabled-text-color));
    }
  `,(0,i.__decorate)([(0,s.MZ)()],c.prototype,"label",void 0),(0,i.__decorate)([(0,s.MZ)()],c.prototype,"position",void 0),c=(0,i.__decorate)([(0,s.EM)("ha-help-tooltip")],c),e()}catch(l){e(l)}}))},81657:function(t,e,a){var i=a(62826),o=a(96196),s=a(77845),r=a(92542);const n=(t,e)=>{const a=(t=>"lovelace"===t.url_path?"panel.states":"profile"===t.url_path?"panel.profile":`panel.${t.title}`)(e);return t.localize(a)||e.title||void 0},l=t=>{if(!t.icon)switch(t.component_name){case"profile":return"mdi:account";case"lovelace":return"mdi:view-dashboard"}return t.icon||void 0};a(34887),a(94343),a(22598);const c=[],d=t=>o.qy`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${t.icon} slot="start"></ha-icon>
    <span slot="headline">${t.title||t.path}</span>
    ${t.title?o.qy`<span slot="supporting-text">${t.path}</span>`:o.s6}
  </ha-combo-box-item>
`,h=(t,e,a)=>{return{path:`/${t}/${e.path??a}`,icon:e.icon??"mdi:view-compact",title:e.title??(e.path?(i=e.path,i.replace(/^_*(.)|_+(.)/g,((t,e,a)=>e?e.toUpperCase():" "+a.toUpperCase()))):`${a}`)};var i},p=(t,e)=>({path:`/${e.url_path}`,icon:l(e)||"mdi:view-dashboard",title:n(t,e)||""});class u extends o.WF{render(){return o.qy`
      <ha-combo-box
        .hass=${this.hass}
        item-value-path="path"
        item-label-path="path"
        .value=${this._value}
        allow-custom-value
        .filteredItems=${this.navigationItems}
        .label=${this.label}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
        .renderer=${d}
        @opened-changed=${this._openedChanged}
        @value-changed=${this._valueChanged}
        @filter-changed=${this._filterChanged}
      >
      </ha-combo-box>
    `}async _openedChanged(t){this._opened=t.detail.value,this._opened&&!this.navigationItemsLoaded&&this._loadNavigationItems()}async _loadNavigationItems(){this.navigationItemsLoaded=!0;const t=Object.entries(this.hass.panels).map((([t,e])=>({id:t,...e}))),e=t.filter((t=>"lovelace"===t.component_name)),a=await Promise.all(e.map((t=>{return(e=this.hass.connection,a="lovelace"===t.url_path?null:t.url_path,i=!0,e.sendMessagePromise({type:"lovelace/config",url_path:a,force:i})).then((e=>[t.id,e])).catch((e=>[t.id,void 0]));var e,a,i}))),i=new Map(a);this.navigationItems=[];for(const o of t){this.navigationItems.push(p(this.hass,o));const t=i.get(o.id);t&&"views"in t&&t.views.forEach(((t,e)=>this.navigationItems.push(h(o.url_path,t,e))))}this.comboBox.filteredItems=this.navigationItems}shouldUpdate(t){return!this._opened||t.has("_opened")}_valueChanged(t){t.stopPropagation(),this._setValue(t.detail.value)}_setValue(t){this.value=t,(0,r.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}_filterChanged(t){const e=t.detail.value.toLowerCase();if(e.length>=2){const t=[];this.navigationItems.forEach((a=>{(a.path.toLowerCase().includes(e)||a.title.toLowerCase().includes(e))&&t.push(a)})),t.length>0?this.comboBox.filteredItems=t:this.comboBox.filteredItems=[]}else this.comboBox.filteredItems=this.navigationItems}get _value(){return this.value||""}constructor(...t){super(...t),this.disabled=!1,this.required=!1,this._opened=!1,this.navigationItemsLoaded=!1,this.navigationItems=c}}u.styles=o.AH`
    ha-icon,
    ha-svg-icon {
      color: var(--primary-text-color);
      position: relative;
      bottom: 0px;
    }
    *[slot="prefix"] {
      margin-right: 8px;
      margin-inline-end: 8px;
      margin-inline-start: initial;
    }
  `,(0,i.__decorate)([(0,s.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)()],u.prototype,"label",void 0),(0,i.__decorate)([(0,s.MZ)()],u.prototype,"value",void 0),(0,i.__decorate)([(0,s.MZ)()],u.prototype,"helper",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"disabled",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"required",void 0),(0,i.__decorate)([(0,s.wk)()],u.prototype,"_opened",void 0),(0,i.__decorate)([(0,s.P)("ha-combo-box",!0)],u.prototype,"comboBox",void 0),u=(0,i.__decorate)([(0,s.EM)("ha-navigation-picker")],u)},28238:function(t,e,a){a.a(t,(async function(t,i){try{a.r(e),a.d(e,{HaSelectorUiAction:()=>d});var o=a(62826),s=a(96196),r=a(77845),n=a(92542),l=a(38020),c=t([l]);l=(c.then?(await c)():c)[0];class d extends s.WF{render(){return s.qy`
      <hui-action-editor
        .label=${this.label}
        .hass=${this.hass}
        .config=${this.value}
        .actions=${this.selector.ui_action?.actions}
        .defaultAction=${this.selector.ui_action?.default_action}
        .tooltipText=${this.helper}
        @value-changed=${this._valueChanged}
      ></hui-action-editor>
    `}_valueChanged(t){t.stopPropagation(),(0,n.r)(this,"value-changed",{value:t.detail.value})}}(0,o.__decorate)([(0,r.MZ)({attribute:!1})],d.prototype,"hass",void 0),(0,o.__decorate)([(0,r.MZ)({attribute:!1})],d.prototype,"selector",void 0),(0,o.__decorate)([(0,r.MZ)({attribute:!1})],d.prototype,"value",void 0),(0,o.__decorate)([(0,r.MZ)()],d.prototype,"label",void 0),(0,o.__decorate)([(0,r.MZ)()],d.prototype,"helper",void 0),d=(0,o.__decorate)([(0,r.EM)("ha-selector-ui_action")],d),i()}catch(d){i(d)}}))},88422:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),o=a(52630),s=a(96196),r=a(77845),n=t([o]);o=(n.then?(await n)():n)[0];class l extends o.A{static get styles(){return[o.A.styles,s.AH`
        :host {
          --wa-tooltip-background-color: var(--secondary-background-color);
          --wa-tooltip-content-color: var(--primary-text-color);
          --wa-tooltip-font-family: var(
            --ha-tooltip-font-family,
            var(--ha-font-family-body)
          );
          --wa-tooltip-font-size: var(
            --ha-tooltip-font-size,
            var(--ha-font-size-s)
          );
          --wa-tooltip-font-weight: var(
            --ha-tooltip-font-weight,
            var(--ha-font-weight-normal)
          );
          --wa-tooltip-line-height: var(
            --ha-tooltip-line-height,
            var(--ha-line-height-condensed)
          );
          --wa-tooltip-padding: 8px;
          --wa-tooltip-border-radius: var(
            --ha-tooltip-border-radius,
            var(--ha-border-radius-sm)
          );
          --wa-tooltip-arrow-size: var(--ha-tooltip-arrow-size, 8px);
          --wa-z-index-tooltip: var(--ha-tooltip-z-index, 1000);
        }
      `]}constructor(...t){super(...t),this.showDelay=150,this.hideDelay=150}}(0,i.__decorate)([(0,r.MZ)({attribute:"show-delay",type:Number})],l.prototype,"showDelay",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:"hide-delay",type:Number})],l.prototype,"hideDelay",void 0),l=(0,i.__decorate)([(0,r.EM)("ha-tooltip")],l),e()}catch(l){e(l)}}))},23362:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),o=a(53289),s=a(96196),r=a(77845),n=a(92542),l=a(4657),c=a(39396),d=a(4848),h=(a(17963),a(89473)),p=a(32884),u=t([h,p]);[h,p]=u.then?(await u)():u;const _=t=>{if("object"!=typeof t||null===t)return!1;for(const e in t)if(Object.prototype.hasOwnProperty.call(t,e))return!1;return!0};class v extends s.WF{setValue(t){try{this._yaml=_(t)?"":(0,o.Bh)(t,{schema:this.yamlSchema,quotingType:'"',noRefs:!0})}catch(e){console.error(e,t),alert(`There was an error converting to YAML: ${e}`)}}firstUpdated(){void 0!==this.defaultValue&&this.setValue(this.defaultValue)}willUpdate(t){super.willUpdate(t),this.autoUpdate&&t.has("value")&&this.setValue(this.value)}focus(){this._codeEditor?.codemirror&&this._codeEditor?.codemirror.focus()}render(){return void 0===this._yaml?s.s6:s.qy`
      ${this.label?s.qy`<p>${this.label}${this.required?" *":""}</p>`:s.s6}
      <ha-code-editor
        .hass=${this.hass}
        .value=${this._yaml}
        .readOnly=${this.readOnly}
        .disableFullscreen=${this.disableFullscreen}
        mode="yaml"
        autocomplete-entities
        autocomplete-icons
        .error=${!1===this.isValid}
        @value-changed=${this._onChange}
        @blur=${this._onBlur}
        dir="ltr"
      ></ha-code-editor>
      ${this._showingError?s.qy`<ha-alert alert-type="error">${this._error}</ha-alert>`:s.s6}
      ${this.copyClipboard||this.hasExtraActions?s.qy`
            <div class="card-actions">
              ${this.copyClipboard?s.qy`
                    <ha-button appearance="plain" @click=${this._copyYaml}>
                      ${this.hass.localize("ui.components.yaml-editor.copy_to_clipboard")}
                    </ha-button>
                  `:s.s6}
              <slot name="extra-actions"></slot>
            </div>
          `:s.s6}
    `}_onChange(t){let e;t.stopPropagation(),this._yaml=t.detail.value;let a,i=!0;if(this._yaml)try{e=(0,o.Hh)(this._yaml,{schema:this.yamlSchema})}catch(s){i=!1,a=`${this.hass.localize("ui.components.yaml-editor.error",{reason:s.reason})}${s.mark?` (${this.hass.localize("ui.components.yaml-editor.error_location",{line:s.mark.line+1,column:s.mark.column+1})})`:""}`}else e={};this._error=a??"",i&&(this._showingError=!1),this.value=e,this.isValid=i,(0,n.r)(this,"value-changed",{value:e,isValid:i,errorMsg:a})}_onBlur(){this.showErrors&&this._error&&(this._showingError=!0)}get yaml(){return this._yaml}async _copyYaml(){this.yaml&&(await(0,l.l)(this.yaml),(0,d.P)(this,{message:this.hass.localize("ui.common.copied_clipboard")}))}static get styles(){return[c.RF,s.AH`
        .card-actions {
          border-radius: var(
            --actions-border-radius,
            var(--ha-border-radius-square) var(--ha-border-radius-square)
              var(--ha-card-border-radius, var(--ha-border-radius-lg))
              var(--ha-card-border-radius, var(--ha-border-radius-lg))
          );
          border: 1px solid var(--divider-color);
          padding: 5px 16px;
        }
        ha-code-editor {
          flex-grow: 1;
          min-height: 0;
        }
      `]}constructor(...t){super(...t),this.yamlSchema=o.my,this.isValid=!0,this.autoUpdate=!1,this.readOnly=!1,this.disableFullscreen=!1,this.required=!1,this.copyClipboard=!1,this.hasExtraActions=!1,this.showErrors=!0,this._yaml="",this._error="",this._showingError=!1}}(0,i.__decorate)([(0,r.MZ)({attribute:!1})],v.prototype,"hass",void 0),(0,i.__decorate)([(0,r.MZ)()],v.prototype,"value",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:!1})],v.prototype,"yamlSchema",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:!1})],v.prototype,"defaultValue",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:"is-valid",type:Boolean})],v.prototype,"isValid",void 0),(0,i.__decorate)([(0,r.MZ)()],v.prototype,"label",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:"auto-update",type:Boolean})],v.prototype,"autoUpdate",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:"read-only",type:Boolean})],v.prototype,"readOnly",void 0),(0,i.__decorate)([(0,r.MZ)({type:Boolean,attribute:"disable-fullscreen"})],v.prototype,"disableFullscreen",void 0),(0,i.__decorate)([(0,r.MZ)({type:Boolean})],v.prototype,"required",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:"copy-clipboard",type:Boolean})],v.prototype,"copyClipboard",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:"has-extra-actions",type:Boolean})],v.prototype,"hasExtraActions",void 0),(0,i.__decorate)([(0,r.MZ)({attribute:"show-errors",type:Boolean})],v.prototype,"showErrors",void 0),(0,i.__decorate)([(0,r.wk)()],v.prototype,"_yaml",void 0),(0,i.__decorate)([(0,r.wk)()],v.prototype,"_error",void 0),(0,i.__decorate)([(0,r.wk)()],v.prototype,"_showingError",void 0),(0,i.__decorate)([(0,r.P)("ha-code-editor")],v.prototype,"_codeEditor",void 0),v=(0,i.__decorate)([(0,r.EM)("ha-yaml-editor")],v),e()}catch(_){e(_)}}))},45369:function(t,e,a){a.d(e,{QC:()=>i,ds:()=>c,mp:()=>r,nx:()=>s,u6:()=>n,vU:()=>o,zn:()=>l});const i=(t,e,a)=>"run-start"===e.type?t={init_options:a,stage:"ready",run:e.data,events:[e],started:new Date(e.timestamp)}:t?((t="wake_word-start"===e.type?{...t,stage:"wake_word",wake_word:{...e.data,done:!1}}:"wake_word-end"===e.type?{...t,wake_word:{...t.wake_word,...e.data,done:!0}}:"stt-start"===e.type?{...t,stage:"stt",stt:{...e.data,done:!1}}:"stt-end"===e.type?{...t,stt:{...t.stt,...e.data,done:!0}}:"intent-start"===e.type?{...t,stage:"intent",intent:{...e.data,done:!1}}:"intent-end"===e.type?{...t,intent:{...t.intent,...e.data,done:!0}}:"tts-start"===e.type?{...t,stage:"tts",tts:{...e.data,done:!1}}:"tts-end"===e.type?{...t,tts:{...t.tts,...e.data,done:!0}}:"run-end"===e.type?{...t,finished:new Date(e.timestamp),stage:"done"}:"error"===e.type?{...t,finished:new Date(e.timestamp),stage:"error",error:e.data}:{...t}).events=[...t.events,e],t):void console.warn("Received unexpected event before receiving session",e),o=(t,e,a)=>t.connection.subscribeMessage(e,{...a,type:"assist_pipeline/run"}),s=t=>t.callWS({type:"assist_pipeline/pipeline/list"}),r=(t,e)=>t.callWS({type:"assist_pipeline/pipeline/get",pipeline_id:e}),n=(t,e)=>t.callWS({type:"assist_pipeline/pipeline/create",...e}),l=(t,e,a)=>t.callWS({type:"assist_pipeline/pipeline/update",pipeline_id:e,...a}),c=t=>t.callWS({type:"assist_pipeline/language/list"})},38020:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),o=a(96196),s=a(77845),r=a(22786),n=a(92542),l=a(55124),c=a(56528),d=a(2076),h=(a(56565),a(81657),a(39338)),p=t([c,d,h]);[c,d,h]=p.then?(await p)():p;const u=["more-info","toggle","navigate","url","perform-action","assist","none"],_=[{name:"navigation_path",selector:{navigation:{}}}],v=[{type:"grid",name:"",schema:[{name:"pipeline_id",selector:{assist_pipeline:{include_last_used:!0}}},{name:"start_listening",selector:{boolean:{}}}]}];class y extends o.WF{get _navigation_path(){const t=this.config;return t?.navigation_path||""}get _url_path(){const t=this.config;return t?.url_path||""}get _service(){const t=this.config;return t?.perform_action||t?.service||""}updated(t){super.updated(t),t.has("defaultAction")&&t.get("defaultAction")!==this.defaultAction&&this._select.layoutOptions()}render(){if(!this.hass)return o.s6;const t=this.actions??u;let e=this.config?.action||"default";return"call-service"===e&&(e="perform-action"),o.qy`
      <div class="dropdown">
        <ha-select
          .label=${this.label}
          .configValue=${"action"}
          @selected=${this._actionPicked}
          .value=${e}
          @closed=${l.d}
          fixedMenuPosition
          naturalMenuWidth
        >
          <ha-list-item value="default">
            ${this.hass.localize("ui.panel.lovelace.editor.action-editor.actions.default_action")}
            ${this.defaultAction?` (${this.hass.localize(`ui.panel.lovelace.editor.action-editor.actions.${this.defaultAction}`).toLowerCase()})`:o.s6}
          </ha-list-item>
          ${t.map((t=>o.qy`
              <ha-list-item .value=${t}>
                ${this.hass.localize(`ui.panel.lovelace.editor.action-editor.actions.${t}`)}
              </ha-list-item>
            `))}
        </ha-select>
        ${this.tooltipText?o.qy`
              <ha-help-tooltip .label=${this.tooltipText}></ha-help-tooltip>
            `:o.s6}
      </div>
      ${"navigate"===this.config?.action?o.qy`
            <ha-form
              .hass=${this.hass}
              .schema=${_}
              .data=${this.config}
              .computeLabel=${this._computeFormLabel}
              @value-changed=${this._formValueChanged}
            >
            </ha-form>
          `:o.s6}
      ${"url"===this.config?.action?o.qy`
            <ha-textfield
              .label=${this.hass.localize("ui.panel.lovelace.editor.action-editor.url_path")}
              .value=${this._url_path}
              .configValue=${"url_path"}
              @input=${this._valueChanged}
            ></ha-textfield>
          `:o.s6}
      ${"call-service"===this.config?.action||"perform-action"===this.config?.action?o.qy`
            <ha-service-control
              .hass=${this.hass}
              .value=${this._serviceAction(this.config)}
              .showAdvanced=${this.hass.userData?.showAdvanced}
              narrow
              @value-changed=${this._serviceValueChanged}
            ></ha-service-control>
          `:o.s6}
      ${"assist"===this.config?.action?o.qy`
            <ha-form
              .hass=${this.hass}
              .schema=${v}
              .data=${this.config}
              .computeLabel=${this._computeFormLabel}
              @value-changed=${this._formValueChanged}
            >
            </ha-form>
          `:o.s6}
    `}_actionPicked(t){if(t.stopPropagation(),!this.hass)return;let e=this.config?.action;"call-service"===e&&(e="perform-action");const a=t.target.value;if(e===a)return;if("default"===a)return void(0,n.r)(this,"value-changed",{value:void 0});let i;switch(a){case"url":i={url_path:this._url_path};break;case"perform-action":i={perform_action:this._service};break;case"navigate":i={navigation_path:this._navigation_path}}(0,n.r)(this,"value-changed",{value:{action:a,...i}})}_valueChanged(t){if(t.stopPropagation(),!this.hass)return;const e=t.target,a=t.target.value??t.target.checked;this[`_${e.configValue}`]!==a&&e.configValue&&(0,n.r)(this,"value-changed",{value:{...this.config,[e.configValue]:a}})}_formValueChanged(t){t.stopPropagation();const e=t.detail.value;(0,n.r)(this,"value-changed",{value:e})}_computeFormLabel(t){return this.hass?.localize(`ui.panel.lovelace.editor.action-editor.${t.name}`)}_serviceValueChanged(t){t.stopPropagation();const e={...this.config,action:"perform-action",perform_action:t.detail.value.action||"",data:t.detail.value.data,target:t.detail.value.target||{}};t.detail.value.data||delete e.data,"service_data"in e&&delete e.service_data,"service"in e&&delete e.service,(0,n.r)(this,"value-changed",{value:e})}constructor(...t){super(...t),this._serviceAction=(0,r.A)((t=>({action:this._service,...t.data||t.service_data?{data:t.data??t.service_data}:null,target:t.target})))}}y.styles=o.AH`
    .dropdown {
      position: relative;
    }
    ha-help-tooltip {
      position: absolute;
      right: 40px;
      top: 16px;
      inset-inline-start: initial;
      inset-inline-end: 40px;
      direction: var(--direction);
    }
    ha-select,
    ha-textfield {
      width: 100%;
    }
    ha-service-control,
    ha-navigation-picker,
    ha-form {
      display: block;
    }
    ha-textfield,
    ha-service-control,
    ha-navigation-picker,
    ha-form {
      margin-top: 8px;
    }
    ha-service-control {
      --service-control-padding: 0;
    }
  `,(0,i.__decorate)([(0,s.MZ)({attribute:!1})],y.prototype,"config",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],y.prototype,"label",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],y.prototype,"actions",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],y.prototype,"defaultAction",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],y.prototype,"tooltipText",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,i.__decorate)([(0,s.P)("ha-select")],y.prototype,"_select",void 0),y=(0,i.__decorate)([(0,s.EM)("hui-action-editor")],y),e()}catch(u){e(u)}}))},62001:function(t,e,a){a.d(e,{o:()=>i});const i=(t,e)=>`https://${t.config.version.includes("b")?"rc":t.config.version.includes("dev")?"next":"www"}.home-assistant.io${e}`},4848:function(t,e,a){a.d(e,{P:()=>o});var i=a(92542);const o=(t,e)=>(0,i.r)(t,"hass-notification",e)},3890:function(t,e,a){a.d(e,{T:()=>p});var i=a(5055),o=a(63937),s=a(37540);class r{disconnect(){this.G=void 0}reconnect(t){this.G=t}deref(){return this.G}constructor(t){this.G=t}}class n{get(){return this.Y}pause(){this.Y??=new Promise((t=>this.Z=t))}resume(){this.Z?.(),this.Y=this.Z=void 0}constructor(){this.Y=void 0,this.Z=void 0}}var l=a(42017);const c=t=>!(0,o.sO)(t)&&"function"==typeof t.then,d=1073741823;class h extends s.Kq{render(...t){return t.find((t=>!c(t)))??i.c0}update(t,e){const a=this._$Cbt;let o=a.length;this._$Cbt=e;const s=this._$CK,r=this._$CX;this.isConnected||this.disconnected();for(let i=0;i<e.length&&!(i>this._$Cwt);i++){const t=e[i];if(!c(t))return this._$Cwt=i,t;i<o&&t===a[i]||(this._$Cwt=d,o=0,Promise.resolve(t).then((async e=>{for(;r.get();)await r.get();const a=s.deref();if(void 0!==a){const i=a._$Cbt.indexOf(t);i>-1&&i<a._$Cwt&&(a._$Cwt=i,a.setValue(e))}})))}return i.c0}disconnected(){this._$CK.disconnect(),this._$CX.pause()}reconnected(){this._$CK.reconnect(this),this._$CX.resume()}constructor(){super(...arguments),this._$Cwt=d,this._$Cbt=[],this._$CK=new r(this),this._$CX=new n}}const p=(0,l.u$)(h)}};
//# sourceMappingURL=9344.bde53b1e145cf581.js.map