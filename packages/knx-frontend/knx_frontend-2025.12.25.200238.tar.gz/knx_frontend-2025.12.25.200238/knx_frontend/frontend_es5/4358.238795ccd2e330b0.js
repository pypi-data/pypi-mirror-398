"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["4358"],{88867:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t),i.d(t,{HaIconPicker:function(){return O}});var o=i(31432),n=i(44734),s=i(56038),r=i(69683),l=i(6454),c=i(61397),d=i(94741),h=i(50264),u=(i(28706),i(2008),i(74423),i(23792),i(62062),i(44114),i(34782),i(26910),i(18111),i(22489),i(7588),i(61701),i(13579),i(26099),i(3362),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(23500),i(62953),i(62826)),p=i(96196),v=i(77845),_=i(22786),g=i(92542),f=i(33978),y=i(55179),m=(i(22598),i(94343),e([y]));y=(m.then?(await m)():m)[0];var b,$,k,x,w,A=e=>e,M=[],q=!1,z=function(){var e=(0,h.A)((0,c.A)().m((function e(){var t,a;return(0,c.A)().w((function(e){for(;;)switch(e.n){case 0:return q=!0,e.n=1,i.e("3451").then(i.t.bind(i,83174,19));case 1:return t=e.v,M=t.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords}))),a=[],Object.keys(f.y).forEach((e=>{a.push(Z(e))})),e.n=2,Promise.all(a);case 2:e.v.forEach((e=>{var t;(t=M).push.apply(t,(0,d.A)(e))}));case 3:return e.a(2)}}),e)})));return function(){return e.apply(this,arguments)}}(),Z=function(){var e=(0,h.A)((0,c.A)().m((function e(t){var i,a,o;return(0,c.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(e.p=0,"function"==typeof(i=f.y[t].getIconList)){e.n=1;break}return e.a(2,[]);case 1:return e.n=2,i();case 2:return a=e.v,o=a.map((e=>{var i;return{icon:`${t}:${e.name}`,parts:new Set(e.name.split("-")),keywords:null!==(i=e.keywords)&&void 0!==i?i:[]}})),e.a(2,o);case 3:return e.p=3,e.v,console.warn(`Unable to load icon list for ${t} iconset`),e.a(2,[])}}),e,null,[[0,3]])})));return function(t){return e.apply(this,arguments)}}(),H=e=>(0,p.qy)(b||(b=A`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${0} slot="start"></ha-icon>
    ${0}
  </ha-combo-box-item>
`),e.icon,e.icon),O=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),s=0;s<i;s++)a[s]=arguments[s];return(e=(0,r.A)(this,t,[].concat(a))).disabled=!1,e.required=!1,e.invalid=!1,e._filterIcons=(0,_.A)((function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:M;if(!e)return t;var i,a=[],n=(e,t)=>a.push({icon:e,rank:t}),s=(0,o.A)(t);try{for(s.s();!(i=s.n()).done;){var r=i.value;r.parts.has(e)?n(r.icon,1):r.keywords.includes(e)?n(r.icon,2):r.icon.includes(e)?n(r.icon,3):r.keywords.some((t=>t.includes(e)))&&n(r.icon,4)}}catch(l){s.e(l)}finally{s.f()}return 0===a.length&&n(e,0),a.sort(((e,t)=>e.rank-t.rank))})),e._iconProvider=(t,i)=>{var a=e._filterIcons(t.filter.toLowerCase(),M),o=t.page*t.pageSize,n=o+t.pageSize;i(a.slice(o,n),a.length)},e}return(0,l.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){return(0,p.qy)($||($=A`
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
    `),this.hass,this._value,q?this._iconProvider:void 0,this.label,this.helper,this.disabled,this.required,this.placeholder,this.errorMessage,this.invalid,H,this._openedChanged,this._valueChanged,this._value||this.placeholder?(0,p.qy)(k||(k=A`
              <ha-icon .icon=${0} slot="icon">
              </ha-icon>
            `),this._value||this.placeholder):(0,p.qy)(x||(x=A`<slot slot="icon" name="fallback"></slot>`)))}},{key:"_openedChanged",value:(i=(0,h.A)((0,c.A)().m((function e(t){return(0,c.A)().w((function(e){for(;;)switch(e.n){case 0:if(!t.detail.value||q){e.n=2;break}return e.n=1,z();case 1:this.requestUpdate();case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_valueChanged",value:function(e){e.stopPropagation(),this._setValue(e.detail.value)}},{key:"_setValue",value:function(e){this.value=e,(0,g.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}},{key:"_value",get:function(){return this.value||""}}]);var i}(p.WF);O.styles=(0,p.AH)(w||(w=A`
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
  `)),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],O.prototype,"hass",void 0),(0,u.__decorate)([(0,v.MZ)()],O.prototype,"value",void 0),(0,u.__decorate)([(0,v.MZ)()],O.prototype,"label",void 0),(0,u.__decorate)([(0,v.MZ)()],O.prototype,"helper",void 0),(0,u.__decorate)([(0,v.MZ)()],O.prototype,"placeholder",void 0),(0,u.__decorate)([(0,v.MZ)({attribute:"error-message"})],O.prototype,"errorMessage",void 0),(0,u.__decorate)([(0,v.MZ)({type:Boolean})],O.prototype,"disabled",void 0),(0,u.__decorate)([(0,v.MZ)({type:Boolean})],O.prototype,"required",void 0),(0,u.__decorate)([(0,v.MZ)({type:Boolean})],O.prototype,"invalid",void 0),O=(0,u.__decorate)([(0,v.EM)("ha-icon-picker")],O),a()}catch(V){a(V)}}))},24933:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t);var o=i(61397),n=i(50264),s=i(94741),r=i(44734),l=i(56038),c=i(69683),d=i(6454),h=(i(28706),i(54554),i(62826)),u=i(96196),p=i(77845),v=i(4937),_=i(92542),g=i(89473),f=(i(60733),i(88867)),y=(i(75261),i(56565),i(63801),i(78740),i(10234)),m=i(39396),b=e([g,f]);[g,f]=b.then?(await b)():b;var $,k,x,w,A=e=>e,M=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,c.A)(this,t,[].concat(a))).new=!1,e.disabled=!1,e._options=[],e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"_optionMoved",value:function(e){e.stopPropagation();var t=e.detail,i=t.oldIndex,a=t.newIndex,o=this._options.concat(),n=o.splice(i,1)[0];o.splice(a,0,n),(0,_.r)(this,"value-changed",{value:Object.assign(Object.assign({},this._item),{},{options:o})})}},{key:"item",set:function(e){this._item=e,e?(this._name=e.name||"",this._icon=e.icon||"",this._options=e.options||[]):(this._name="",this._icon="",this._options=[])}},{key:"focus",value:function(){this.updateComplete.then((()=>{var e;return null===(e=this.shadowRoot)||void 0===e||null===(e=e.querySelector("[dialogInitialFocus]"))||void 0===e?void 0:e.focus()}))}},{key:"render",value:function(){return this.hass?(0,u.qy)($||($=A`
      <div class="form">
        <ha-textfield
          dialogInitialFocus
          autoValidate
          required
          .validationMessage=${0}
          .value=${0}
          .label=${0}
          .configValue=${0}
          @input=${0}
          .disabled=${0}
        ></ha-textfield>
        <ha-icon-picker
          .hass=${0}
          .value=${0}
          .configValue=${0}
          @value-changed=${0}
          .label=${0}
          .disabled=${0}
        ></ha-icon-picker>
        <div class="header">
          ${0}:
        </div>
        <ha-sortable
          @item-moved=${0}
          handle-selector=".handle"
          .disabled=${0}
        >
          <ha-list class="options">
            ${0}
          </ha-list>
        </ha-sortable>
        <div class="layout horizontal center">
          <ha-textfield
            class="flex-auto"
            id="option_input"
            .label=${0}
            @keydown=${0}
            .disabled=${0}
          ></ha-textfield>
          <ha-button
            size="small"
            appearance="plain"
            @click=${0}
            .disabled=${0}
            >${0}</ha-button
          >
        </div>
      </div>
    `),this.hass.localize("ui.dialogs.helper_settings.required_error_msg"),this._name,this.hass.localize("ui.dialogs.helper_settings.generic.name"),"name",this._valueChanged,this.disabled,this.hass,this._icon,"icon",this._valueChanged,this.hass.localize("ui.dialogs.helper_settings.generic.icon"),this.disabled,this.hass.localize("ui.dialogs.helper_settings.input_select.options"),this._optionMoved,this.disabled,this._options.length?(0,v.u)(this._options,(e=>e),((e,t)=>(0,u.qy)(k||(k=A`
                    <ha-list-item class="option" hasMeta>
                      <div class="optioncontent">
                        <div class="handle">
                          <ha-svg-icon
                            .path=${0}
                          ></ha-svg-icon>
                        </div>
                        ${0}
                      </div>
                      <ha-icon-button
                        slot="meta"
                        .index=${0}
                        .label=${0}
                        @click=${0}
                        .disabled=${0}
                        .path=${0}
                      ></ha-icon-button>
                    </ha-list-item>
                  `),"M21 11H3V9H21V11M21 13H3V15H21V13Z",e,t,this.hass.localize("ui.dialogs.helper_settings.input_select.remove_option"),this._removeOption,this.disabled,"M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"))):(0,u.qy)(x||(x=A`
                  <ha-list-item noninteractive>
                    ${0}
                  </ha-list-item>
                `),this.hass.localize("ui.dialogs.helper_settings.input_select.no_options")),this.hass.localize("ui.dialogs.helper_settings.input_select.add_option"),this._handleKeyAdd,this.disabled,this._addOption,this.disabled,this.hass.localize("ui.dialogs.helper_settings.input_select.add")):u.s6}},{key:"_handleKeyAdd",value:function(e){e.stopPropagation(),"Enter"===e.key&&this._addOption()}},{key:"_addOption",value:function(){var e=this._optionInput;null!=e&&e.value&&((0,_.r)(this,"value-changed",{value:Object.assign(Object.assign({},this._item),{},{options:[].concat((0,s.A)(this._options),[e.value])})}),e.value="")}},{key:"_removeOption",value:(i=(0,n.A)((0,o.A)().m((function e(t){var i,a;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:return i=t.target.index,e.n=1,(0,y.dk)(this,{title:this.hass.localize("ui.dialogs.helper_settings.input_select.confirm_delete.delete"),text:this.hass.localize("ui.dialogs.helper_settings.input_select.confirm_delete.prompt"),destructive:!0});case 1:if(e.v){e.n=2;break}return e.a(2);case 2:(a=(0,s.A)(this._options)).splice(i,1),(0,_.r)(this,"value-changed",{value:Object.assign(Object.assign({},this._item),{},{options:a})});case 3:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_valueChanged",value:function(e){var t;if(this.new||this._item){e.stopPropagation();var i=e.target.configValue,a=(null===(t=e.detail)||void 0===t?void 0:t.value)||e.target.value;if(this[`_${i}`]!==a){var o=Object.assign({},this._item);a?o[i]=a:delete o[i],(0,_.r)(this,"value-changed",{value:o})}}}}],[{key:"styles",get:function(){return[m.RF,(0,u.AH)(w||(w=A`
        .form {
          color: var(--primary-text-color);
        }
        .option {
          border: 1px solid var(--divider-color);
          border-radius: var(--ha-border-radius-sm);
          margin-top: 4px;
          --mdc-icon-button-size: 24px;
          --mdc-ripple-color: transparent;
          --mdc-list-side-padding: 16px;
          cursor: default;
          background-color: var(--card-background-color);
        }
        ha-textfield {
          display: block;
          margin-bottom: 8px;
        }
        #option_input {
          margin-top: 8px;
        }
        .header {
          margin-top: 8px;
          margin-bottom: 8px;
        }
        .handle {
          cursor: move; /* fallback if grab cursor is unsupported */
          cursor: grab;
          padding-right: 12px;
          padding-inline-end: 12px;
          padding-inline-start: initial;
        }
        .handle ha-svg-icon {
          pointer-events: none;
          height: 24px;
        }
        .optioncontent {
          display: flex;
          align-items: center;
        }
      `))]}}]);var i}(u.WF);(0,h.__decorate)([(0,p.MZ)({attribute:!1})],M.prototype,"hass",void 0),(0,h.__decorate)([(0,p.MZ)({type:Boolean})],M.prototype,"new",void 0),(0,h.__decorate)([(0,p.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,h.__decorate)([(0,p.wk)()],M.prototype,"_name",void 0),(0,h.__decorate)([(0,p.wk)()],M.prototype,"_icon",void 0),(0,h.__decorate)([(0,p.wk)()],M.prototype,"_options",void 0),(0,h.__decorate)([(0,p.P)("#option_input",!0)],M.prototype,"_optionInput",void 0),M=(0,h.__decorate)([(0,p.EM)("ha-input_select-form")],M),a()}catch(q){a(q)}}))}}]);
//# sourceMappingURL=4358.238795ccd2e330b0.js.map