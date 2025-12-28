/*! For license information please see 6211.1d8bd450713817f9.js.LICENSE.txt */
"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["6211"],{45783:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),n=i(56038),s=i(69683),r=i(6454),o=(i(28706),i(62826)),l=i(96196),h=i(77845),c=i(92542),u=i(9316),d=e([u]);u=(d.then?(await d)():d)[0];var p,_=e=>e,v=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,n=new Array(i),r=0;r<i;r++)n[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(n))).disabled=!1,e}return(0,r.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){return this.aliases?(0,l.qy)(p||(p=_`
      <ha-multi-textfield
        .hass=${0}
        .value=${0}
        .disabled=${0}
        .label=${0}
        .removeLabel=${0}
        .addLabel=${0}
        item-index
        @value-changed=${0}
      >
      </ha-multi-textfield>
    `),this.hass,this.aliases,this.disabled,this.hass.localize("ui.dialogs.aliases.label"),this.hass.localize("ui.dialogs.aliases.remove"),this.hass.localize("ui.dialogs.aliases.add"),this._aliasesChanged):l.s6}},{key:"_aliasesChanged",value:function(e){(0,c.r)(this,"value-changed",{value:e})}}])}(l.WF);(0,o.__decorate)([(0,h.MZ)({attribute:!1})],v.prototype,"hass",void 0),(0,o.__decorate)([(0,h.MZ)({type:Array})],v.prototype,"aliases",void 0),(0,o.__decorate)([(0,h.MZ)({type:Boolean})],v.prototype,"disabled",void 0),v=(0,o.__decorate)([(0,h.EM)("ha-aliases-editor")],v),t()}catch(y){t(y)}}))},88867:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t),i.d(t,{HaIconPicker:function(){return Z}});var n=i(31432),s=i(44734),r=i(56038),o=i(69683),l=i(6454),h=i(61397),c=i(94741),u=i(50264),d=(i(28706),i(2008),i(74423),i(23792),i(62062),i(44114),i(34782),i(26910),i(18111),i(22489),i(7588),i(61701),i(13579),i(26099),i(3362),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(23500),i(62953),i(62826)),p=i(96196),_=i(77845),v=i(22786),y=i(92542),f=i(33978),m=i(55179),g=(i(22598),i(94343),e([m]));m=(g.then?(await g)():g)[0];var $,k,b,w,A,C=e=>e,x=[],z=!1,E=function(){var e=(0,u.A)((0,h.A)().m((function e(){var t,a;return(0,h.A)().w((function(e){for(;;)switch(e.n){case 0:return z=!0,e.n=1,i.e("3451").then(i.t.bind(i,83174,19));case 1:return t=e.v,x=t.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords}))),a=[],Object.keys(f.y).forEach((e=>{a.push(q(e))})),e.n=2,Promise.all(a);case 2:e.v.forEach((e=>{var t;(t=x).push.apply(t,(0,c.A)(e))}));case 3:return e.a(2)}}),e)})));return function(){return e.apply(this,arguments)}}(),q=function(){var e=(0,u.A)((0,h.A)().m((function e(t){var i,a,n;return(0,h.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(e.p=0,"function"==typeof(i=f.y[t].getIconList)){e.n=1;break}return e.a(2,[]);case 1:return e.n=2,i();case 2:return a=e.v,n=a.map((e=>{var i;return{icon:`${t}:${e.name}`,parts:new Set(e.name.split("-")),keywords:null!==(i=e.keywords)&&void 0!==i?i:[]}})),e.a(2,n);case 3:return e.p=3,e.v,console.warn(`Unable to load icon list for ${t} iconset`),e.a(2,[])}}),e,null,[[0,3]])})));return function(t){return e.apply(this,arguments)}}(),M=e=>(0,p.qy)($||($=C`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${0} slot="start"></ha-icon>
    ${0}
  </ha-combo-box-item>
`),e.icon,e.icon),Z=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,o.A)(this,t,[].concat(a))).disabled=!1,e.required=!1,e.invalid=!1,e._filterIcons=(0,v.A)((function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:x;if(!e)return t;var i,a=[],s=(e,t)=>a.push({icon:e,rank:t}),r=(0,n.A)(t);try{for(r.s();!(i=r.n()).done;){var o=i.value;o.parts.has(e)?s(o.icon,1):o.keywords.includes(e)?s(o.icon,2):o.icon.includes(e)?s(o.icon,3):o.keywords.some((t=>t.includes(e)))&&s(o.icon,4)}}catch(l){r.e(l)}finally{r.f()}return 0===a.length&&s(e,0),a.sort(((e,t)=>e.rank-t.rank))})),e._iconProvider=(t,i)=>{var a=e._filterIcons(t.filter.toLowerCase(),x),n=t.page*t.pageSize,s=n+t.pageSize;i(a.slice(n,s),a.length)},e}return(0,l.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){return(0,p.qy)(k||(k=C`
      <ha-combo-box
        .hass=${0}
        item-value-path="icon"
        item-label-path="icon"
        .value=${0}
        allow-custom-value
        .dataProvider=${0}
        .label=${0}
        .helper=${0}
        .disabled=${0}
        .required=${0}
        .placeholder=${0}
        .errorMessage=${0}
        .invalid=${0}
        .renderer=${0}
        icon
        @opened-changed=${0}
        @value-changed=${0}
      >
        ${0}
      </ha-combo-box>
    `),this.hass,this._value,z?this._iconProvider:void 0,this.label,this.helper,this.disabled,this.required,this.placeholder,this.errorMessage,this.invalid,M,this._openedChanged,this._valueChanged,this._value||this.placeholder?(0,p.qy)(b||(b=C`
              <ha-icon .icon=${0} slot="icon">
              </ha-icon>
            `),this._value||this.placeholder):(0,p.qy)(w||(w=C`<slot slot="icon" name="fallback"></slot>`)))}},{key:"_openedChanged",value:(i=(0,u.A)((0,h.A)().m((function e(t){return(0,h.A)().w((function(e){for(;;)switch(e.n){case 0:if(!t.detail.value||z){e.n=2;break}return e.n=1,E();case 1:this.requestUpdate();case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_valueChanged",value:function(e){e.stopPropagation(),this._setValue(e.detail.value)}},{key:"_setValue",value:function(e){this.value=e,(0,y.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}},{key:"_value",get:function(){return this.value||""}}]);var i}(p.WF);Z.styles=(0,p.AH)(A||(A=C`
    *[slot="icon"] {
      color: var(--primary-text-color);
      position: relative;
      bottom: 2px;
    }
    *[slot="prefix"] {
      margin-right: 8px;
      margin-inline-end: 8px;
      margin-inline-start: initial;
    }
  `)),(0,d.__decorate)([(0,_.MZ)({attribute:!1})],Z.prototype,"hass",void 0),(0,d.__decorate)([(0,_.MZ)()],Z.prototype,"value",void 0),(0,d.__decorate)([(0,_.MZ)()],Z.prototype,"label",void 0),(0,d.__decorate)([(0,_.MZ)()],Z.prototype,"helper",void 0),(0,d.__decorate)([(0,_.MZ)()],Z.prototype,"placeholder",void 0),(0,d.__decorate)([(0,_.MZ)({attribute:"error-message"})],Z.prototype,"errorMessage",void 0),(0,d.__decorate)([(0,_.MZ)({type:Boolean})],Z.prototype,"disabled",void 0),(0,d.__decorate)([(0,_.MZ)({type:Boolean})],Z.prototype,"required",void 0),(0,d.__decorate)([(0,_.MZ)({type:Boolean})],Z.prototype,"invalid",void 0),Z=(0,d.__decorate)([(0,_.EM)("ha-icon-picker")],Z),a()}catch(D){a(D)}}))},71437:function(e,t,i){i.d(t,{Sn:function(){return a},q2:function(){return n},tb:function(){return s}});i(61397),i(50264);var a="timestamp",n="temperature",s="humidity"},76218:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t);var n=i(61397),s=i(50264),r=i(44734),o=i(56038),l=i(69683),h=i(6454),c=(i(28706),i(42762),i(62826)),u=i(96196),d=i(77845),p=i(92542),_=i(82965),v=(i(17963),i(45783)),y=i(95637),f=i(76894),m=i(88867),g=i(32649),$=i(41881),k=(i(2809),i(78740),i(54110)),b=i(71437),w=i(10234),A=i(39396),C=e([_,v,f,m,g,$]);[_,v,f,m,g,$]=C.then?(await C)():C;var x,z,E,q,M,Z,D,F,P=e=>e,S={round:!1,type:"image/jpeg",quality:.75},G=["sensor"],I=[b.q2],K=[b.tb],V=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,l.A)(this,t,[].concat(a)))._areaEntityFilter=t=>{var i=e.hass.entities[t.entity_id];if(!i)return!1;var a=e._params.entry.area_id;if(i.area_id===a)return!0;if(!i.device_id)return!1;var n=e.hass.devices[i.device_id];return n&&n.area_id===a},e}return(0,h.A)(t,e),(0,o.A)(t,[{key:"showDialog",value:(c=(0,s.A)((0,n.A)().m((function e(t){return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:return this._params=t,this._error=void 0,this._params.entry?(this._name=this._params.entry.name,this._aliases=this._params.entry.aliases,this._labels=this._params.entry.labels,this._picture=this._params.entry.picture,this._icon=this._params.entry.icon,this._floor=this._params.entry.floor_id,this._temperatureEntity=this._params.entry.temperature_entity_id,this._humidityEntity=this._params.entry.humidity_entity_id):(this._name=this._params.suggestedName||"",this._aliases=[],this._labels=[],this._picture=null,this._icon=null,this._floor=null,this._temperatureEntity=null,this._humidityEntity=null),e.n=1,this.updateComplete;case 1:return e.a(2)}}),e,this)}))),function(e){return c.apply(this,arguments)})},{key:"closeDialog",value:function(){this._error="",this._params=void 0,(0,p.r)(this,"dialog-closed",{dialog:this.localName})}},{key:"_renderSettings",value:function(e){return(0,u.qy)(x||(x=P`
      ${0}

      <ha-textfield
        .value=${0}
        @input=${0}
        .label=${0}
        .validationMessage=${0}
        required
        dialogInitialFocus
      ></ha-textfield>

      <ha-icon-picker
        .hass=${0}
        .value=${0}
        @value-changed=${0}
        .label=${0}
      ></ha-icon-picker>

      <ha-floor-picker
        .hass=${0}
        .value=${0}
        @value-changed=${0}
        .label=${0}
      ></ha-floor-picker>

      <ha-labels-picker
        .label=${0}
        .hass=${0}
        .value=${0}
        @value-changed=${0}
        .placeholder=${0}
      ></ha-labels-picker>

      <ha-picture-upload
        .hass=${0}
        .value=${0}
        crop
        select-media
        .cropOptions=${0}
        @change=${0}
      ></ha-picture-upload>
    `),e?(0,u.qy)(z||(z=P`
            <ha-settings-row>
              <span slot="heading">
                ${0}
              </span>
              <span slot="description"> ${0} </span>
            </ha-settings-row>
          `),this.hass.localize("ui.panel.config.areas.editor.area_id"),e.area_id):u.s6,this._name,this._nameChanged,this.hass.localize("ui.panel.config.areas.editor.name"),this.hass.localize("ui.panel.config.areas.editor.name_required"),this.hass,this._icon,this._iconChanged,this.hass.localize("ui.panel.config.areas.editor.icon"),this.hass,this._floor,this._floorChanged,this.hass.localize("ui.panel.config.areas.editor.floor"),this.hass.localize("ui.components.label-picker.labels"),this.hass,this._labels,this._labelsChanged,this.hass.localize("ui.panel.config.areas.editor.add_labels"),this.hass,this._picture,S,this._pictureChanged)}},{key:"_renderAliasExpansion",value:function(){return(0,u.qy)(E||(E=P`
      <ha-expansion-panel
        outlined
        .header=${0}
        expanded
      >
        <div class="content">
          <p class="description">
            ${0}
          </p>
          <ha-aliases-editor
            .hass=${0}
            .aliases=${0}
            @value-changed=${0}
          ></ha-aliases-editor>
        </div>
      </ha-expansion-panel>
    `),this.hass.localize("ui.panel.config.areas.editor.aliases_section"),this.hass.localize("ui.panel.config.areas.editor.aliases_description"),this.hass,this._aliases,this._aliasesChanged)}},{key:"_renderRelatedEntitiesExpansion",value:function(){return(0,u.qy)(q||(q=P`
      <ha-expansion-panel
        outlined
        .header=${0}
        expanded
      >
        <div class="content">
          <ha-entity-picker
            .hass=${0}
            .label=${0}
            .helper=${0}
            .value=${0}
            .includeDomains=${0}
            .includeDeviceClasses=${0}
            .entityFilter=${0}
            @value-changed=${0}
          ></ha-entity-picker>

          <ha-entity-picker
            .hass=${0}
            .label=${0}
            .helper=${0}
            .value=${0}
            .includeDomains=${0}
            .includeDeviceClasses=${0}
            .entityFilter=${0}
            @value-changed=${0}
          ></ha-entity-picker>
        </div>
      </ha-expansion-panel>
    `),this.hass.localize("ui.panel.config.areas.editor.related_entities_section"),this.hass,this.hass.localize("ui.panel.config.areas.editor.temperature_entity"),this.hass.localize("ui.panel.config.areas.editor.temperature_entity_description"),this._temperatureEntity,G,I,this._areaEntityFilter,this._sensorChanged,this.hass,this.hass.localize("ui.panel.config.areas.editor.humidity_entity"),this.hass.localize("ui.panel.config.areas.editor.humidity_entity_description"),this._humidityEntity,G,K,this._areaEntityFilter,this._sensorChanged)}},{key:"render",value:function(){if(!this._params)return u.s6;var e=this._params.entry,t=!this._isNameValid(),i=!e;return(0,u.qy)(M||(M=P`
      <ha-dialog
        open
        @closed=${0}
        .heading=${0}
      >
        <div>
          ${0}
          <div class="form">
            ${0} ${0}
            ${0}
          </div>
        </div>
        ${0}
        <ha-button
          slot="primaryAction"
          @click=${0}
          .disabled=${0}
        >
          ${0}
        </ha-button>
      </ha-dialog>
    `),this.closeDialog,(0,y.l)(this.hass,e?this.hass.localize("ui.panel.config.areas.editor.update_area"):this.hass.localize("ui.panel.config.areas.editor.create_area")),this._error?(0,u.qy)(Z||(Z=P`<ha-alert alert-type="error">${0}</ha-alert>`),this._error):"",this._renderSettings(e),this._renderAliasExpansion(),i?u.s6:this._renderRelatedEntitiesExpansion(),i?u.s6:(0,u.qy)(D||(D=P`<ha-button
              slot="secondaryAction"
              variant="danger"
              appearance="plain"
              @click=${0}
            >
              ${0}
            </ha-button>`),this._deleteArea,this.hass.localize("ui.common.delete")),this._updateEntry,t||!!this._submitting,e?this.hass.localize("ui.common.save"):this.hass.localize("ui.common.create"))}},{key:"_isNameValid",value:function(){return""!==this._name.trim()}},{key:"_nameChanged",value:function(e){this._error=void 0,this._name=e.target.value}},{key:"_floorChanged",value:function(e){this._error=void 0,this._floor=e.detail.value}},{key:"_iconChanged",value:function(e){this._error=void 0,this._icon=e.detail.value}},{key:"_labelsChanged",value:function(e){this._error=void 0,this._labels=e.detail.value}},{key:"_pictureChanged",value:function(e){this._error=void 0,this._picture=e.target.value}},{key:"_aliasesChanged",value:function(e){this._aliases=e.detail.value}},{key:"_sensorChanged",value:function(e){this[`_${e.target.includeDeviceClasses[0]}Entity`]=e.detail.value||null}},{key:"_updateEntry",value:(a=(0,s.A)((0,n.A)().m((function e(){var t,i,a;return(0,n.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(t=!this._params.entry,this._submitting=!0,e.p=1,i={name:this._name.trim(),picture:this._picture||(t?void 0:null),icon:this._icon||(t?void 0:null),floor_id:this._floor||(t?void 0:null),labels:this._labels||null,aliases:this._aliases,temperature_entity_id:this._temperatureEntity,humidity_entity_id:this._humidityEntity},!t){e.n=3;break}return e.n=2,this._params.createEntry(i);case 2:e.n=4;break;case 3:return e.n=4,this._params.updateEntry(i);case 4:this.closeDialog(),e.n=6;break;case 5:e.p=5,a=e.v,this._error=a.message||this.hass.localize("ui.panel.config.areas.editor.unknown_error");case 6:return e.p=6,this._submitting=!1,e.f(6);case 7:return e.a(2)}}),e,this,[[1,5,6,7]])}))),function(){return a.apply(this,arguments)})},{key:"_deleteArea",value:(i=(0,s.A)((0,n.A)().m((function e(){var t;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:if(null!==(t=this._params)&&void 0!==t&&t.entry){e.n=1;break}return e.a(2);case 1:return e.n=2,(0,w.dk)(this,{title:this.hass.localize("ui.panel.config.areas.delete.confirmation_title",{name:this._params.entry.name}),text:this.hass.localize("ui.panel.config.areas.delete.confirmation_text"),dismissText:this.hass.localize("ui.common.cancel"),confirmText:this.hass.localize("ui.common.delete"),destructive:!0});case 2:if(e.v){e.n=3;break}return e.a(2);case 3:return e.n=4,(0,k.uG)(this.hass,this._params.entry.area_id);case 4:this.closeDialog();case 5:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})}],[{key:"styles",get:function(){return[A.nA,(0,u.AH)(F||(F=P`
        ha-textfield {
          display: block;
        }
        ha-expansion-panel {
          --expansion-panel-content-padding: 0;
        }
        ha-aliases-editor,
        ha-entity-picker,
        ha-floor-picker,
        ha-icon-picker,
        ha-labels-picker,
        ha-picture-upload,
        ha-expansion-panel {
          display: block;
          margin-bottom: 16px;
        }
        ha-dialog {
          --mdc-dialog-min-width: min(600px, 100vw);
        }
        .content {
          padding: 12px;
        }
        .description {
          margin: 0 0 16px 0;
        }
      `))]}}]);var i,a,c}(u.WF);(0,c.__decorate)([(0,d.MZ)({attribute:!1})],V.prototype,"hass",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_name",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_aliases",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_labels",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_picture",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_icon",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_floor",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_temperatureEntity",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_humidityEntity",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_error",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_params",void 0),(0,c.__decorate)([(0,d.wk)()],V.prototype,"_submitting",void 0),customElements.define("dialog-area-registry-detail",V),a()}catch(Y){a(Y)}}))},45847:function(e,t,i){i.d(t,{T:function(){return g}});var a=i(61397),n=i(50264),s=i(44734),r=i(56038),o=i(75864),l=i(69683),h=i(6454),c=(i(50113),i(25276),i(18111),i(20116),i(26099),i(3362),i(4610)),u=i(63937),d=i(37540);i(52675),i(89463),i(66412),i(16280),i(23792),i(62953);var p=function(){return(0,r.A)((function e(t){(0,s.A)(this,e),this.G=t}),[{key:"disconnect",value:function(){this.G=void 0}},{key:"reconnect",value:function(e){this.G=e}},{key:"deref",value:function(){return this.G}}])}(),_=function(){return(0,r.A)((function e(){(0,s.A)(this,e),this.Y=void 0,this.Z=void 0}),[{key:"get",value:function(){return this.Y}},{key:"pause",value:function(){var e;null!==(e=this.Y)&&void 0!==e||(this.Y=new Promise((e=>this.Z=e)))}},{key:"resume",value:function(){var e;null!==(e=this.Z)&&void 0!==e&&e.call(this),this.Y=this.Z=void 0}}])}(),v=i(42017),y=e=>!(0,u.sO)(e)&&"function"==typeof e.then,f=1073741823,m=function(e){function t(){var e;return(0,s.A)(this,t),(e=(0,l.A)(this,t,arguments))._$Cwt=f,e._$Cbt=[],e._$CK=new p((0,o.A)(e)),e._$CX=new _,e}return(0,h.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){for(var e,t=arguments.length,i=new Array(t),a=0;a<t;a++)i[a]=arguments[a];return null!==(e=i.find((e=>!y(e))))&&void 0!==e?e:c.c0}},{key:"update",value:function(e,t){var i=this,s=this._$Cbt,r=s.length;this._$Cbt=t;var o=this._$CK,l=this._$CX;this.isConnected||this.disconnected();for(var h,u=function(){var e=t[d];if(!y(e))return{v:(i._$Cwt=d,e)};d<r&&e===s[d]||(i._$Cwt=f,r=0,Promise.resolve(e).then(function(){var t=(0,n.A)((0,a.A)().m((function t(i){var n,s;return(0,a.A)().w((function(t){for(;;)switch(t.n){case 0:if(!l.get()){t.n=2;break}return t.n=1,l.get();case 1:t.n=0;break;case 2:void 0!==(n=o.deref())&&(s=n._$Cbt.indexOf(e))>-1&&s<n._$Cwt&&(n._$Cwt=s,n.setValue(i));case 3:return t.a(2)}}),t)})));return function(e){return t.apply(this,arguments)}}()))},d=0;d<t.length&&!(d>this._$Cwt);d++)if(h=u())return h.v;return c.c0}},{key:"disconnected",value:function(){this._$CK.disconnect(),this._$CX.pause()}},{key:"reconnected",value:function(){this._$CK.reconnect(this),this._$CX.resume()}}])}(d.Kq),g=(0,v.u$)(m)}}]);
//# sourceMappingURL=6211.1d8bd450713817f9.js.map