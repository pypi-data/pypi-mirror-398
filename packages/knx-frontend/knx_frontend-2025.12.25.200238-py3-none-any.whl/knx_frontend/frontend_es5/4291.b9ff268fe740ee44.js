"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["4291"],{41278:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(61397),a=o(50264),n=o(44734),r=o(56038),s=o(69683),l=o(6454),d=(o(28706),o(62062),o(26910),o(18111),o(61701),o(26099),o(62826)),c=o(96196),u=o(77845),h=o(92542),p=o(25749),_=o(3950),v=o(84125),y=o(76681),f=o(55179),g=(o(94343),e([f]));f=(g.then?(await g)():g)[0];var b,m,k=e=>e,$=function(e){function t(){var e;(0,n.A)(this,t);for(var o=arguments.length,i=new Array(o),a=0;a<o;a++)i[a]=arguments[a];return(e=(0,s.A)(this,t,[].concat(i))).value="",e.disabled=!1,e.required=!1,e._rowRenderer=t=>{var o;return(0,c.qy)(b||(b=k`
    <ha-combo-box-item type="button">
      <span slot="headline">
        ${0}
      </span>
      <span slot="supporting-text">${0}</span>
      <img
        alt=""
        slot="start"
        src=${0}
        crossorigin="anonymous"
        referrerpolicy="no-referrer"
        @error=${0}
        @load=${0}
      />
    </ha-combo-box-item>
  `),t.title||e.hass.localize("ui.panel.config.integrations.config_entry.unnamed_entry"),t.localized_domain_name,(0,y.MR)({domain:t.domain,type:"icon",darkOptimized:null===(o=e.hass.themes)||void 0===o?void 0:o.darkMode}),e._onImageError,e._onImageLoad)},e}return(0,l.A)(t,e),(0,r.A)(t,[{key:"open",value:function(){var e;null===(e=this._comboBox)||void 0===e||e.open()}},{key:"focus",value:function(){var e;null===(e=this._comboBox)||void 0===e||e.focus()}},{key:"firstUpdated",value:function(){this._getConfigEntries()}},{key:"render",value:function(){return this._configEntries?(0,c.qy)(m||(m=k`
      <ha-combo-box
        .hass=${0}
        .label=${0}
        .value=${0}
        .required=${0}
        .disabled=${0}
        .helper=${0}
        .renderer=${0}
        .items=${0}
        item-value-path="entry_id"
        item-id-path="entry_id"
        item-label-path="title"
        @value-changed=${0}
      ></ha-combo-box>
    `),this.hass,void 0===this.label&&this.hass?this.hass.localize("ui.components.config-entry-picker.config_entry"):this.label,this._value,this.required,this.disabled,this.helper,this._rowRenderer,this._configEntries,this._valueChanged):c.s6}},{key:"_onImageLoad",value:function(e){e.target.style.visibility="initial"}},{key:"_onImageError",value:function(e){e.target.style.visibility="hidden"}},{key:"_getConfigEntries",value:(o=(0,a.A)((0,i.A)().m((function e(){return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:(0,_.VN)(this.hass,{type:["device","hub","service"],domain:this.integration}).then((e=>{this._configEntries=e.map((e=>Object.assign(Object.assign({},e),{},{localized_domain_name:(0,v.p$)(this.hass.localize,e.domain)}))).sort(((e,t)=>(0,p.SH)(e.localized_domain_name+e.title,t.localized_domain_name+t.title,this.hass.locale.language)))}));case 1:return e.a(2)}}),e,this)}))),function(){return o.apply(this,arguments)})},{key:"_value",get:function(){return this.value||""}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;t!==this._value&&this._setValue(t)}},{key:"_setValue",value:function(e){this.value=e,setTimeout((()=>{(0,h.r)(this,"value-changed",{value:e}),(0,h.r)(this,"change")}),0)}}]);var o}(c.WF);(0,d.__decorate)([(0,u.MZ)()],$.prototype,"integration",void 0),(0,d.__decorate)([(0,u.MZ)()],$.prototype,"label",void 0),(0,d.__decorate)([(0,u.MZ)()],$.prototype,"value",void 0),(0,d.__decorate)([(0,u.MZ)()],$.prototype,"helper",void 0),(0,d.__decorate)([(0,u.wk)()],$.prototype,"_configEntries",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],$.prototype,"disabled",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],$.prototype,"required",void 0),(0,d.__decorate)([(0,u.P)("ha-combo-box")],$.prototype,"_comboBox",void 0),$=(0,d.__decorate)([(0,u.EM)("ha-config-entry-picker")],$),t()}catch(M){t(M)}}))},6286:function(e,t,o){o.a(e,(async function(e,i){try{o.r(t),o.d(t,{HaConfigEntrySelector:function(){return y}});var a=o(44734),n=o(56038),r=o(69683),s=o(6454),l=(o(28706),o(62826)),d=o(96196),c=o(77845),u=o(41278),h=e([u]);u=(h.then?(await h)():h)[0];var p,_,v=e=>e,y=function(e){function t(){var e;(0,a.A)(this,t);for(var o=arguments.length,i=new Array(o),n=0;n<o;n++)i[n]=arguments[n];return(e=(0,r.A)(this,t,[].concat(i))).disabled=!1,e.required=!0,e}return(0,s.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){var e;return(0,d.qy)(p||(p=v`<ha-config-entry-picker
      .hass=${0}
      .value=${0}
      .label=${0}
      .helper=${0}
      .disabled=${0}
      .required=${0}
      .integration=${0}
      allow-custom-entity
    ></ha-config-entry-picker>`),this.hass,this.value,this.label,this.helper,this.disabled,this.required,null===(e=this.selector.config_entry)||void 0===e?void 0:e.integration)}}])}(d.WF);y.styles=(0,d.AH)(_||(_=v`
    ha-config-entry-picker {
      width: 100%;
    }
  `)),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"selector",void 0),(0,l.__decorate)([(0,c.MZ)()],y.prototype,"value",void 0),(0,l.__decorate)([(0,c.MZ)()],y.prototype,"label",void 0),(0,l.__decorate)([(0,c.MZ)()],y.prototype,"helper",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"disabled",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"required",void 0),y=(0,l.__decorate)([(0,c.EM)("ha-selector-config_entry")],y),i()}catch(f){i(f)}}))},76681:function(e,t,o){o.d(t,{MR:function(){return i},a_:function(){return a},bg:function(){return n}});var i=e=>`https://brands.home-assistant.io/${e.brand?"brands/":""}${e.useFallback?"_/":""}${e.domain}/${e.darkOptimized?"dark_":""}${e.type}.png`,a=e=>e.split("/")[4],n=e=>e.startsWith("https://brands.home-assistant.io/")}}]);
//# sourceMappingURL=4291.b9ff268fe740ee44.js.map