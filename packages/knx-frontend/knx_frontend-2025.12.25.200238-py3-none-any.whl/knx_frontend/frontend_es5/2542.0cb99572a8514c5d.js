"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["2542"],{45783:function(e,a,i){i.a(e,(async function(e,a){try{var t=i(44734),r=i(56038),o=i(69683),s=i(6454),n=(i(28706),i(62826)),l=i(96196),h=i(77845),d=i(92542),c=i(9316),u=e([c]);c=(u.then?(await u)():u)[0];var p,_=e=>e,v=function(e){function a(){var e;(0,t.A)(this,a);for(var i=arguments.length,r=new Array(i),s=0;s<i;s++)r[s]=arguments[s];return(e=(0,o.A)(this,a,[].concat(r))).disabled=!1,e}return(0,s.A)(a,e),(0,r.A)(a,[{key:"render",value:function(){return this.aliases?(0,l.qy)(p||(p=_`
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
    `),this.hass,this.aliases,this.disabled,this.hass.localize("ui.dialogs.aliases.label"),this.hass.localize("ui.dialogs.aliases.remove"),this.hass.localize("ui.dialogs.aliases.add"),this._aliasesChanged):l.s6}},{key:"_aliasesChanged",value:function(e){(0,d.r)(this,"value-changed",{value:e})}}])}(l.WF);(0,n.__decorate)([(0,h.MZ)({attribute:!1})],v.prototype,"hass",void 0),(0,n.__decorate)([(0,h.MZ)({type:Array})],v.prototype,"aliases",void 0),(0,n.__decorate)([(0,h.MZ)({type:Boolean})],v.prototype,"disabled",void 0),v=(0,n.__decorate)([(0,h.EM)("ha-aliases-editor")],v),a()}catch(f){a(f)}}))},88867:function(e,a,i){i.a(e,(async function(e,t){try{i.r(a),i.d(a,{HaIconPicker:function(){return L}});var r=i(31432),o=i(44734),s=i(56038),n=i(69683),l=i(6454),h=i(61397),d=i(94741),c=i(50264),u=(i(28706),i(2008),i(74423),i(23792),i(62062),i(44114),i(34782),i(26910),i(18111),i(22489),i(7588),i(61701),i(13579),i(26099),i(3362),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(23500),i(62953),i(62826)),p=i(96196),_=i(77845),v=i(22786),f=i(92542),y=i(33978),m=i(55179),g=(i(22598),i(94343),e([m]));m=(g.then?(await g)():g)[0];var $,A,b,k,w,M=e=>e,x=[],z=!1,q=function(){var e=(0,c.A)((0,h.A)().m((function e(){var a,t;return(0,h.A)().w((function(e){for(;;)switch(e.n){case 0:return z=!0,e.n=1,i.e("3451").then(i.t.bind(i,83174,19));case 1:return a=e.v,x=a.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords}))),t=[],Object.keys(y.y).forEach((e=>{t.push(C(e))})),e.n=2,Promise.all(t);case 2:e.v.forEach((e=>{var a;(a=x).push.apply(a,(0,d.A)(e))}));case 3:return e.a(2)}}),e)})));return function(){return e.apply(this,arguments)}}(),C=function(){var e=(0,c.A)((0,h.A)().m((function e(a){var i,t,r;return(0,h.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(e.p=0,"function"==typeof(i=y.y[a].getIconList)){e.n=1;break}return e.a(2,[]);case 1:return e.n=2,i();case 2:return t=e.v,r=t.map((e=>{var i;return{icon:`${a}:${e.name}`,parts:new Set(e.name.split("-")),keywords:null!==(i=e.keywords)&&void 0!==i?i:[]}})),e.a(2,r);case 3:return e.p=3,e.v,console.warn(`Unable to load icon list for ${a} iconset`),e.a(2,[])}}),e,null,[[0,3]])})));return function(a){return e.apply(this,arguments)}}(),Z=e=>(0,p.qy)($||($=M`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${0} slot="start"></ha-icon>
    ${0}
  </ha-combo-box-item>
`),e.icon,e.icon),L=function(e){function a(){var e;(0,o.A)(this,a);for(var i=arguments.length,t=new Array(i),s=0;s<i;s++)t[s]=arguments[s];return(e=(0,n.A)(this,a,[].concat(t))).disabled=!1,e.required=!1,e.invalid=!1,e._filterIcons=(0,v.A)((function(e){var a=arguments.length>1&&void 0!==arguments[1]?arguments[1]:x;if(!e)return a;var i,t=[],o=(e,a)=>t.push({icon:e,rank:a}),s=(0,r.A)(a);try{for(s.s();!(i=s.n()).done;){var n=i.value;n.parts.has(e)?o(n.icon,1):n.keywords.includes(e)?o(n.icon,2):n.icon.includes(e)?o(n.icon,3):n.keywords.some((a=>a.includes(e)))&&o(n.icon,4)}}catch(l){s.e(l)}finally{s.f()}return 0===t.length&&o(e,0),t.sort(((e,a)=>e.rank-a.rank))})),e._iconProvider=(a,i)=>{var t=e._filterIcons(a.filter.toLowerCase(),x),r=a.page*a.pageSize,o=r+a.pageSize;i(t.slice(r,o),t.length)},e}return(0,l.A)(a,e),(0,s.A)(a,[{key:"render",value:function(){return(0,p.qy)(A||(A=M`
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
    `),this.hass,this._value,z?this._iconProvider:void 0,this.label,this.helper,this.disabled,this.required,this.placeholder,this.errorMessage,this.invalid,Z,this._openedChanged,this._valueChanged,this._value||this.placeholder?(0,p.qy)(b||(b=M`
              <ha-icon .icon=${0} slot="icon">
              </ha-icon>
            `),this._value||this.placeholder):(0,p.qy)(k||(k=M`<slot slot="icon" name="fallback"></slot>`)))}},{key:"_openedChanged",value:(i=(0,c.A)((0,h.A)().m((function e(a){return(0,h.A)().w((function(e){for(;;)switch(e.n){case 0:if(!a.detail.value||z){e.n=2;break}return e.n=1,q();case 1:this.requestUpdate();case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_valueChanged",value:function(e){e.stopPropagation(),this._setValue(e.detail.value)}},{key:"_setValue",value:function(e){this.value=e,(0,f.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}},{key:"_value",get:function(){return this.value||""}}]);var i}(p.WF);L.styles=(0,p.AH)(w||(w=M`
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
  `)),(0,u.__decorate)([(0,_.MZ)({attribute:!1})],L.prototype,"hass",void 0),(0,u.__decorate)([(0,_.MZ)()],L.prototype,"value",void 0),(0,u.__decorate)([(0,_.MZ)()],L.prototype,"label",void 0),(0,u.__decorate)([(0,_.MZ)()],L.prototype,"helper",void 0),(0,u.__decorate)([(0,_.MZ)()],L.prototype,"placeholder",void 0),(0,u.__decorate)([(0,_.MZ)({attribute:"error-message"})],L.prototype,"errorMessage",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean})],L.prototype,"disabled",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean})],L.prototype,"required",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean})],L.prototype,"invalid",void 0),L=(0,u.__decorate)([(0,_.EM)("ha-icon-picker")],L),t()}catch(E){t(E)}}))},96573:function(e,a,i){i.a(e,(async function(e,t){try{i.r(a);var r=i(61397),o=i(50264),s=i(44734),n=i(56038),l=i(69683),h=i(6454),d=(i(28706),i(2008),i(23792),i(62062),i(18111),i(22489),i(61701),i(2892),i(26099),i(16034),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(42762),i(62953),i(62826)),c=i(96196),u=i(77845),p=i(4937),_=i(22786),v=i(92542),f=(i(96294),i(25388),i(17963),i(45783)),y=i(53907),m=i(89473),g=i(95637),$=i(88867),A=i(41881),b=(i(2809),i(60961),i(78740),i(54110)),k=i(39396),w=i(82160),M=e([f,y,m,$,A]);[f,y,m,$,A]=M.then?(await M)():M;var x,z,q,C,Z,L,E,S,V,H,P=e=>e,B=function(e){function a(){var e;(0,s.A)(this,a);for(var i=arguments.length,t=new Array(i),r=0;r<i;r++)t[r]=arguments[r];return(e=(0,l.A)(this,a,[].concat(t)))._addedAreas=new Set,e._removedAreas=new Set,e._floorAreas=(0,_.A)(((e,a,i,t)=>Object.values(a).filter((a=>(a.floor_id===(null==e?void 0:e.floor_id)||i.has(a.area_id))&&!t.has(a.area_id))))),e}return(0,h.A)(a,e),(0,n.A)(a,[{key:"showDialog",value:function(e){var a,i,t,r;this._params=e,this._error=void 0,this._name=this._params.entry?this._params.entry.name:this._params.suggestedName||"",this._aliases=(null===(a=this._params.entry)||void 0===a?void 0:a.aliases)||[],this._icon=(null===(i=this._params.entry)||void 0===i?void 0:i.icon)||null,this._level=null!==(t=null===(r=this._params.entry)||void 0===r?void 0:r.level)&&void 0!==t?t:null,this._addedAreas.clear(),this._removedAreas.clear()}},{key:"closeDialog",value:function(){this._error="",this._params=void 0,this._addedAreas.clear(),this._removedAreas.clear(),(0,v.r)(this,"dialog-closed",{dialog:this.localName})}},{key:"render",value:function(){var e,a=this._floorAreas(null===(e=this._params)||void 0===e?void 0:e.entry,this.hass.areas,this._addedAreas,this._removedAreas);if(!this._params)return c.s6;var i=this._params.entry,t=!this._isNameValid();return(0,c.qy)(x||(x=P`
      <ha-dialog
        open
        @closed=${0}
        .heading=${0}
      >
        <div>
          ${0}
          <div class="form">
            ${0}

            <ha-textfield
              .value=${0}
              @input=${0}
              .label=${0}
              .validationMessage=${0}
              required
              dialogInitialFocus
            ></ha-textfield>

            <ha-textfield
              .value=${0}
              @input=${0}
              .label=${0}
              type="number"
              .helper=${0}
              helperPersistent
            ></ha-textfield>

            <ha-icon-picker
              .hass=${0}
              .value=${0}
              @value-changed=${0}
              .label=${0}
            >
              ${0}
            </ha-icon-picker>

            <h3 class="header">
              ${0}
            </h3>

            ${0}
            <ha-area-picker
              no-add
              .hass=${0}
              @value-changed=${0}
              .excludeAreas=${0}
              .addButtonLabel=${0}
            ></ha-area-picker>

            <h3 class="header">
              ${0}
            </h3>

            <p class="description">
              ${0}
            </p>
            <ha-aliases-editor
              .hass=${0}
              .aliases=${0}
              @value-changed=${0}
            ></ha-aliases-editor>
          </div>
        </div>
        <ha-button
          appearance="plain"
          slot="secondaryAction"
          @click=${0}
        >
          ${0}
        </ha-button>
        <ha-button
          slot="primaryAction"
          @click=${0}
          .disabled=${0}
        >
          ${0}
        </ha-button>
      </ha-dialog>
    `),this.closeDialog,(0,g.l)(this.hass,i?this.hass.localize("ui.panel.config.floors.editor.update_floor"):this.hass.localize("ui.panel.config.floors.editor.create_floor")),this._error?(0,c.qy)(z||(z=P`<ha-alert alert-type="error">${0}</ha-alert>`),this._error):"",i?(0,c.qy)(q||(q=P`
                  <ha-settings-row>
                    <span slot="heading">
                      ${0}
                    </span>
                    <span slot="description">${0}</span>
                  </ha-settings-row>
                `),this.hass.localize("ui.panel.config.floors.editor.floor_id"),i.floor_id):c.s6,this._name,this._nameChanged,this.hass.localize("ui.panel.config.floors.editor.name"),this.hass.localize("ui.panel.config.floors.editor.name_required"),this._level,this._levelChanged,this.hass.localize("ui.panel.config.floors.editor.level"),this.hass.localize("ui.panel.config.floors.editor.level_helper"),this.hass,this._icon,this._iconChanged,this.hass.localize("ui.panel.config.areas.editor.icon"),this._icon?c.s6:(0,c.qy)(C||(C=P`
                    <ha-floor-icon
                      slot="fallback"
                      .floor=${0}
                    ></ha-floor-icon>
                  `),{level:this._level}),this.hass.localize("ui.panel.config.floors.editor.areas_section"),a.length?(0,c.qy)(Z||(Z=P`<ha-chip-set>
                  ${0}
                </ha-chip-set>`),(0,p.u)(a,(e=>e.area_id),(e=>(0,c.qy)(L||(L=P`<ha-input-chip
                        .area=${0}
                        @click=${0}
                        @remove=${0}
                        .label=${0}
                      >
                        ${0}
                      </ha-input-chip>`),e,this._openArea,this._removeArea,null==e?void 0:e.name,e.icon?(0,c.qy)(E||(E=P`<ha-icon
                              slot="icon"
                              .icon=${0}
                            ></ha-icon>`),e.icon):(0,c.qy)(S||(S=P`<ha-svg-icon
                              slot="icon"
                              .path=${0}
                            ></ha-svg-icon>`),"M20 2H4C2.9 2 2 2.9 2 4V20C2 21.11 2.9 22 4 22H20C21.11 22 22 21.11 22 20V4C22 2.9 21.11 2 20 2M4 6L6 4H10.9L4 10.9V6M4 13.7L13.7 4H18.6L4 18.6V13.7M20 18L18 20H13.1L20 13.1V18M20 10.3L10.3 20H5.4L20 5.4V10.3Z"))))):(0,c.qy)(V||(V=P`<p class="description">
                  ${0}
                </p>`),this.hass.localize("ui.panel.config.floors.editor.areas_description")),this.hass,this._addArea,a.map((e=>e.area_id)),this.hass.localize("ui.panel.config.floors.editor.add_area"),this.hass.localize("ui.panel.config.floors.editor.aliases_section"),this.hass.localize("ui.panel.config.floors.editor.aliases_description"),this.hass,this._aliases,this._aliasesChanged,this.closeDialog,this.hass.localize("ui.common.cancel"),this._updateEntry,t||!!this._submitting,i?this.hass.localize("ui.common.save"):this.hass.localize("ui.common.create"))}},{key:"_openArea",value:function(e){var a=e.target.area;(0,w.J)(this,{entry:a,updateEntry:e=>(0,b.gs)(this.hass,a.area_id,e)})}},{key:"_removeArea",value:function(e){var a=e.target.area.area_id;if(this._addedAreas.has(a))return this._addedAreas.delete(a),void(this._addedAreas=new Set(this._addedAreas));this._removedAreas.add(a),this._removedAreas=new Set(this._removedAreas)}},{key:"_addArea",value:function(e){var a=e.detail.value;if(a){if(e.target.value="",this._removedAreas.has(a))return this._removedAreas.delete(a),void(this._removedAreas=new Set(this._removedAreas));this._addedAreas.add(a),this._addedAreas=new Set(this._addedAreas)}}},{key:"_isNameValid",value:function(){return""!==this._name.trim()}},{key:"_nameChanged",value:function(e){this._error=void 0,this._name=e.target.value}},{key:"_levelChanged",value:function(e){this._error=void 0,this._level=""===e.target.value?null:Number(e.target.value)}},{key:"_iconChanged",value:function(e){this._error=void 0,this._icon=e.detail.value}},{key:"_updateEntry",value:(i=(0,o.A)((0,r.A)().m((function e(){var a,i,t;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(this._submitting=!0,a=!this._params.entry,e.p=1,i={name:this._name.trim(),icon:this._icon||(a?void 0:null),level:this._level,aliases:this._aliases},!a){e.n=3;break}return e.n=2,this._params.createEntry(i,this._addedAreas);case 2:e.n=4;break;case 3:return e.n=4,this._params.updateEntry(i,this._addedAreas,this._removedAreas);case 4:this.closeDialog(),e.n=6;break;case 5:e.p=5,t=e.v,this._error=t.message||this.hass.localize("ui.panel.config.floors.editor.unknown_error");case 6:return e.p=6,this._submitting=!1,e.f(6);case 7:return e.a(2)}}),e,this,[[1,5,6,7]])}))),function(){return i.apply(this,arguments)})},{key:"_aliasesChanged",value:function(e){this._aliases=e.detail.value}}],[{key:"styles",get:function(){return[k.RF,k.nA,(0,c.AH)(H||(H=P`
        ha-textfield {
          display: block;
          margin-bottom: 16px;
        }
        ha-floor-icon {
          color: var(--secondary-text-color);
        }
        ha-chip-set {
          margin-bottom: 8px;
        }
      `))]}}]);var i}(c.WF);(0,d.__decorate)([(0,u.MZ)({attribute:!1})],B.prototype,"hass",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_name",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_aliases",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_icon",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_level",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_error",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_params",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_submitting",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_addedAreas",void 0),(0,d.__decorate)([(0,u.wk)()],B.prototype,"_removedAreas",void 0),customElements.define("dialog-floor-registry-detail",B),t()}catch(D){t(D)}}))}}]);
//# sourceMappingURL=2542.0cb99572a8514c5d.js.map