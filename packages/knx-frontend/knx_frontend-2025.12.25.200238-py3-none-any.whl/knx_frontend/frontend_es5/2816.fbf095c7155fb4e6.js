"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["2816"],{60977:function(e,t,i){i.a(e,(async function(e,t){try{var r=i(61397),a=i(50264),o=i(44734),s=i(56038),n=i(69683),c=i(6454),d=i(25460),l=(i(28706),i(23792),i(62062),i(18111),i(61701),i(53921),i(26099),i(62826)),u=i(96196),v=i(77845),h=i(22786),p=i(92542),y=i(56403),_=i(16727),f=i(13877),b=i(3950),m=i(1491),$=i(76681),g=i(96943),k=e([g]);g=(k.then?(await k)():k)[0];var A,M,D,Z,w,q,F,x,C,E=e=>e,L=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,r=new Array(i),a=0;a<i;a++)r[a]=arguments[a];return(e=(0,n.A)(this,t,[].concat(r))).autofocus=!1,e.disabled=!1,e.required=!1,e.hideClearIcon=!1,e._configEntryLookup={},e._getDevicesMemoized=(0,h.A)(m.oG),e._getItems=()=>e._getDevicesMemoized(e.hass,e._configEntryLookup,e.includeDomains,e.excludeDomains,e.includeDeviceClasses,e.deviceFilter,e.entityFilter,e.excludeDevices,e.value),e._valueRenderer=(0,h.A)((t=>i=>{var r,a=i,o=e.hass.devices[a];if(!o)return(0,u.qy)(A||(A=E`<span slot="headline">${0}</span>`),a);var s=(0,f.w)(o,e.hass).area,n=o?(0,_.xn)(o):void 0,c=s?(0,y.A)(s):void 0,d=o.primary_config_entry?t[o.primary_config_entry]:void 0;return(0,u.qy)(M||(M=E`
        ${0}
        <span slot="headline">${0}</span>
        <span slot="supporting-text">${0}</span>
      `),d?(0,u.qy)(D||(D=E`<img
              slot="start"
              alt=""
              crossorigin="anonymous"
              referrerpolicy="no-referrer"
              src=${0}
            />`),(0,$.MR)({domain:d.domain,type:"icon",darkOptimized:null===(r=e.hass.themes)||void 0===r?void 0:r.darkMode})):u.s6,n,c)})),e._rowRenderer=t=>(0,u.qy)(Z||(Z=E`
    <ha-combo-box-item type="button">
      ${0}

      <span slot="headline">${0}</span>
      ${0}
      ${0}
    </ha-combo-box-item>
  `),t.domain?(0,u.qy)(w||(w=E`
            <img
              slot="start"
              alt=""
              crossorigin="anonymous"
              referrerpolicy="no-referrer"
              src=${0}
            />
          `),(0,$.MR)({domain:t.domain,type:"icon",darkOptimized:e.hass.themes.darkMode})):u.s6,t.primary,t.secondary?(0,u.qy)(q||(q=E`<span slot="supporting-text">${0}</span>`),t.secondary):u.s6,t.domain_name?(0,u.qy)(F||(F=E`
            <div slot="trailing-supporting-text" class="domain">
              ${0}
            </div>
          `),t.domain_name):u.s6),e._notFoundLabel=t=>e.hass.localize("ui.components.device-picker.no_match",{term:(0,u.qy)(x||(x=E`<b>‘${0}’</b>`),t)}),e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"firstUpdated",value:function(e){(0,d.A)(t,"firstUpdated",this,3)([e]),this._loadConfigEntries()}},{key:"_loadConfigEntries",value:(l=(0,a.A)((0,r.A)().m((function e(){var t;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,b.VN)(this.hass);case 1:t=e.v,this._configEntryLookup=Object.fromEntries(t.map((e=>[e.entry_id,e])));case 2:return e.a(2)}}),e,this)}))),function(){return l.apply(this,arguments)})},{key:"render",value:function(){var e,t=null!==(e=this.placeholder)&&void 0!==e?e:this.hass.localize("ui.components.device-picker.placeholder"),i=this._valueRenderer(this._configEntryLookup);return(0,u.qy)(C||(C=E`
      <ha-generic-picker
        .hass=${0}
        .autofocus=${0}
        .label=${0}
        .searchLabel=${0}
        .notFoundLabel=${0}
        .emptyLabel=${0}
        .placeholder=${0}
        .value=${0}
        .rowRenderer=${0}
        .getItems=${0}
        .hideClearIcon=${0}
        .valueRenderer=${0}
        @value-changed=${0}
      >
      </ha-generic-picker>
    `),this.hass,this.autofocus,this.label,this.searchLabel,this._notFoundLabel,this.hass.localize("ui.components.device-picker.no_devices"),t,this.value,this._rowRenderer,this._getItems,this.hideClearIcon,i,this._valueChanged)}},{key:"open",value:(i=(0,a.A)((0,r.A)().m((function e(){var t;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.updateComplete;case 1:return e.n=2,null===(t=this._picker)||void 0===t?void 0:t.open();case 2:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;this.value=t,(0,p.r)(this,"value-changed",{value:t})}}]);var i,l}(u.WF);(0,l.__decorate)([(0,v.MZ)({attribute:!1})],L.prototype,"hass",void 0),(0,l.__decorate)([(0,v.MZ)({type:Boolean})],L.prototype,"autofocus",void 0),(0,l.__decorate)([(0,v.MZ)({type:Boolean})],L.prototype,"disabled",void 0),(0,l.__decorate)([(0,v.MZ)({type:Boolean})],L.prototype,"required",void 0),(0,l.__decorate)([(0,v.MZ)()],L.prototype,"label",void 0),(0,l.__decorate)([(0,v.MZ)()],L.prototype,"value",void 0),(0,l.__decorate)([(0,v.MZ)()],L.prototype,"helper",void 0),(0,l.__decorate)([(0,v.MZ)()],L.prototype,"placeholder",void 0),(0,l.__decorate)([(0,v.MZ)({type:String,attribute:"search-label"})],L.prototype,"searchLabel",void 0),(0,l.__decorate)([(0,v.MZ)({attribute:!1,type:Array})],L.prototype,"createDomains",void 0),(0,l.__decorate)([(0,v.MZ)({type:Array,attribute:"include-domains"})],L.prototype,"includeDomains",void 0),(0,l.__decorate)([(0,v.MZ)({type:Array,attribute:"exclude-domains"})],L.prototype,"excludeDomains",void 0),(0,l.__decorate)([(0,v.MZ)({type:Array,attribute:"include-device-classes"})],L.prototype,"includeDeviceClasses",void 0),(0,l.__decorate)([(0,v.MZ)({type:Array,attribute:"exclude-devices"})],L.prototype,"excludeDevices",void 0),(0,l.__decorate)([(0,v.MZ)({attribute:!1})],L.prototype,"deviceFilter",void 0),(0,l.__decorate)([(0,v.MZ)({attribute:!1})],L.prototype,"entityFilter",void 0),(0,l.__decorate)([(0,v.MZ)({attribute:"hide-clear-icon",type:Boolean})],L.prototype,"hideClearIcon",void 0),(0,l.__decorate)([(0,v.P)("ha-generic-picker")],L.prototype,"_picker",void 0),(0,l.__decorate)([(0,v.wk)()],L.prototype,"_configEntryLookup",void 0),L=(0,l.__decorate)([(0,v.EM)("ha-device-picker")],L),t()}catch(I){t(I)}}))},55212:function(e,t,i){i.a(e,(async function(e,t){try{var r=i(94741),a=i(61397),o=i(50264),s=i(44734),n=i(56038),c=i(69683),d=i(6454),l=(i(28706),i(2008),i(74423),i(62062),i(18111),i(22489),i(61701),i(26099),i(62826)),u=i(96196),v=i(77845),h=i(92542),p=i(60977),y=e([p]);p=(y.then?(await y)():y)[0];var _,f,b,m=e=>e,$=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,r=new Array(i),a=0;a<i;a++)r[a]=arguments[a];return(e=(0,c.A)(this,t,[].concat(r))).disabled=!1,e.required=!1,e}return(0,d.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){if(!this.hass)return u.s6;var e=this._currentDevices;return(0,u.qy)(_||(_=m`
      ${0}
      <div>
        <ha-device-picker
          allow-custom-entity
          .hass=${0}
          .helper=${0}
          .deviceFilter=${0}
          .entityFilter=${0}
          .includeDomains=${0}
          .excludeDomains=${0}
          .excludeDevices=${0}
          .includeDeviceClasses=${0}
          .label=${0}
          .disabled=${0}
          .required=${0}
          @value-changed=${0}
        ></ha-device-picker>
      </div>
    `),e.map((e=>(0,u.qy)(f||(f=m`
          <div>
            <ha-device-picker
              allow-custom-entity
              .curValue=${0}
              .hass=${0}
              .deviceFilter=${0}
              .entityFilter=${0}
              .includeDomains=${0}
              .excludeDomains=${0}
              .includeDeviceClasses=${0}
              .value=${0}
              .label=${0}
              .disabled=${0}
              @value-changed=${0}
            ></ha-device-picker>
          </div>
        `),e,this.hass,this.deviceFilter,this.entityFilter,this.includeDomains,this.excludeDomains,this.includeDeviceClasses,e,this.pickedDeviceLabel,this.disabled,this._deviceChanged))),this.hass,this.helper,this.deviceFilter,this.entityFilter,this.includeDomains,this.excludeDomains,e,this.includeDeviceClasses,this.pickDeviceLabel,this.disabled,this.required&&!e.length,this._addDevice)}},{key:"_currentDevices",get:function(){return this.value||[]}},{key:"_updateDevices",value:(l=(0,o.A)((0,a.A)().m((function e(t){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:(0,h.r)(this,"value-changed",{value:t}),this.value=t;case 1:return e.a(2)}}),e,this)}))),function(e){return l.apply(this,arguments)})},{key:"_deviceChanged",value:function(e){e.stopPropagation();var t=e.currentTarget.curValue,i=e.detail.value;i!==t&&(void 0===i?this._updateDevices(this._currentDevices.filter((e=>e!==t))):this._updateDevices(this._currentDevices.map((e=>e===t?i:e))))}},{key:"_addDevice",value:(i=(0,o.A)((0,a.A)().m((function e(t){var i,o;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:if(t.stopPropagation(),i=t.detail.value,t.currentTarget.value="",i){e.n=1;break}return e.a(2);case 1:if(!(o=this._currentDevices).includes(i)){e.n=2;break}return e.a(2);case 2:this._updateDevices([].concat((0,r.A)(o),[i]));case 3:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})}]);var i,l}(u.WF);$.styles=(0,u.AH)(b||(b=m`
    div {
      margin-top: 8px;
    }
  `)),(0,l.__decorate)([(0,v.MZ)({attribute:!1})],$.prototype,"hass",void 0),(0,l.__decorate)([(0,v.MZ)({type:Array})],$.prototype,"value",void 0),(0,l.__decorate)([(0,v.MZ)()],$.prototype,"helper",void 0),(0,l.__decorate)([(0,v.MZ)({type:Boolean})],$.prototype,"disabled",void 0),(0,l.__decorate)([(0,v.MZ)({type:Boolean})],$.prototype,"required",void 0),(0,l.__decorate)([(0,v.MZ)({type:Array,attribute:"include-domains"})],$.prototype,"includeDomains",void 0),(0,l.__decorate)([(0,v.MZ)({type:Array,attribute:"exclude-domains"})],$.prototype,"excludeDomains",void 0),(0,l.__decorate)([(0,v.MZ)({type:Array,attribute:"include-device-classes"})],$.prototype,"includeDeviceClasses",void 0),(0,l.__decorate)([(0,v.MZ)({attribute:"picked-device-label"})],$.prototype,"pickedDeviceLabel",void 0),(0,l.__decorate)([(0,v.MZ)({attribute:"pick-device-label"})],$.prototype,"pickDeviceLabel",void 0),(0,l.__decorate)([(0,v.MZ)({attribute:!1})],$.prototype,"deviceFilter",void 0),(0,l.__decorate)([(0,v.MZ)({attribute:!1})],$.prototype,"entityFilter",void 0),$=(0,l.__decorate)([(0,v.EM)("ha-devices-picker")],$),t()}catch(g){t(g)}}))},95907:function(e,t,i){i.a(e,(async function(e,r){try{i.r(t),i.d(t,{HaDeviceSelector:function(){return Z}});var a=i(44734),o=i(56038),s=i(69683),n=i(6454),c=i(25460),d=(i(28706),i(2008),i(18111),i(22489),i(13579),i(26099),i(16034),i(62826)),l=i(96196),u=i(77845),v=i(22786),h=i(55376),p=i(92542),y=i(1491),_=i(28441),f=i(3950),b=i(82694),m=i(60977),$=i(55212),g=e([m,$]);[m,$]=g.then?(await g)():g;var k,A,M,D=e=>e,Z=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,r=new Array(i),o=0;o<i;o++)r[o]=arguments[o];return(e=(0,s.A)(this,t,[].concat(r))).disabled=!1,e.required=!0,e._deviceIntegrationLookup=(0,v.A)(y.fk),e._filterDevices=t=>{var i;if(null===(i=e.selector.device)||void 0===i||!i.filter)return!0;var r=e._entitySources?e._deviceIntegrationLookup(e._entitySources,Object.values(e.hass.entities),Object.values(e.hass.devices),e._configEntries):void 0;return(0,h.e)(e.selector.device.filter).some((e=>(0,b.vX)(e,t,r)))},e._filterEntities=t=>(0,h.e)(e.selector.device.entity).some((i=>(0,b.Ru)(i,t,e._entitySources))),e}return(0,n.A)(t,e),(0,o.A)(t,[{key:"_hasIntegration",value:function(e){var t,i;return(null===(t=e.device)||void 0===t?void 0:t.filter)&&(0,h.e)(e.device.filter).some((e=>e.integration))||(null===(i=e.device)||void 0===i?void 0:i.entity)&&(0,h.e)(e.device.entity).some((e=>e.integration))}},{key:"willUpdate",value:function(e){var t,i;e.get("selector")&&void 0!==this.value&&(null!==(t=this.selector.device)&&void 0!==t&&t.multiple&&!Array.isArray(this.value)?(this.value=[this.value],(0,p.r)(this,"value-changed",{value:this.value})):null!==(i=this.selector.device)&&void 0!==i&&i.multiple||!Array.isArray(this.value)||(this.value=this.value[0],(0,p.r)(this,"value-changed",{value:this.value})))}},{key:"updated",value:function(e){(0,c.A)(t,"updated",this,3)([e]),e.has("selector")&&this._hasIntegration(this.selector)&&!this._entitySources&&(0,_.c)(this.hass).then((e=>{this._entitySources=e})),!this._configEntries&&this._hasIntegration(this.selector)&&(this._configEntries=[],(0,f.VN)(this.hass).then((e=>{this._configEntries=e})))}},{key:"render",value:function(){var e,t,i;return this._hasIntegration(this.selector)&&!this._entitySources?l.s6:null!==(e=this.selector.device)&&void 0!==e&&e.multiple?(0,l.qy)(A||(A=D`
      ${0}
      <ha-devices-picker
        .hass=${0}
        .value=${0}
        .helper=${0}
        .deviceFilter=${0}
        .entityFilter=${0}
        .disabled=${0}
        .required=${0}
      ></ha-devices-picker>
    `),this.label?(0,l.qy)(M||(M=D`<label>${0}</label>`),this.label):"",this.hass,this.value,this.helper,this._filterDevices,null!==(t=this.selector.device)&&void 0!==t&&t.entity?this._filterEntities:void 0,this.disabled,this.required):(0,l.qy)(k||(k=D`
        <ha-device-picker
          .hass=${0}
          .value=${0}
          .label=${0}
          .helper=${0}
          .deviceFilter=${0}
          .entityFilter=${0}
          .placeholder=${0}
          .disabled=${0}
          .required=${0}
          allow-custom-entity
        ></ha-device-picker>
      `),this.hass,this.value,this.label,this.helper,this._filterDevices,null!==(i=this.selector.device)&&void 0!==i&&i.entity?this._filterEntities:void 0,this.placeholder,this.disabled,this.required)}}])}(l.WF);(0,d.__decorate)([(0,u.MZ)({attribute:!1})],Z.prototype,"hass",void 0),(0,d.__decorate)([(0,u.MZ)({attribute:!1})],Z.prototype,"selector",void 0),(0,d.__decorate)([(0,u.wk)()],Z.prototype,"_entitySources",void 0),(0,d.__decorate)([(0,u.wk)()],Z.prototype,"_configEntries",void 0),(0,d.__decorate)([(0,u.MZ)()],Z.prototype,"value",void 0),(0,d.__decorate)([(0,u.MZ)()],Z.prototype,"label",void 0),(0,d.__decorate)([(0,u.MZ)()],Z.prototype,"helper",void 0),(0,d.__decorate)([(0,u.MZ)()],Z.prototype,"placeholder",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],Z.prototype,"disabled",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],Z.prototype,"required",void 0),Z=(0,d.__decorate)([(0,u.EM)("ha-selector-device")],Z),r()}catch(w){r(w)}}))},28441:function(e,t,i){i.d(t,{c:function(){return n}});var r=i(61397),a=i(50264),o=(i(28706),i(26099),i(3362),function(){var e=(0,a.A)((0,r.A)().m((function e(t,i,a,s,n){var c,d,l,u,v,h,p,y=arguments;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:for(c=y.length,d=new Array(c>5?c-5:0),l=5;l<c;l++)d[l-5]=y[l];if(v=(u=n)[t],h=e=>s&&s(n,e.result)!==e.cacheKey?(u[t]=void 0,o.apply(void 0,[t,i,a,s,n].concat(d))):e.result,!v){e.n=1;break}return e.a(2,v instanceof Promise?v.then(h):h(v));case 1:return p=a.apply(void 0,[n].concat(d)),u[t]=p,p.then((e=>{u[t]={result:e,cacheKey:null==s?void 0:s(n,e)},setTimeout((()=>{u[t]=void 0}),i)}),(()=>{u[t]=void 0})),e.a(2,p)}}),e)})));return function(t,i,r,a,o){return e.apply(this,arguments)}}()),s=e=>e.callWS({type:"entity/source"}),n=e=>o("_entitySources",3e4,s,(e=>Object.keys(e.states).length),e)},76681:function(e,t,i){i.d(t,{MR:function(){return r},a_:function(){return a},bg:function(){return o}});var r=e=>`https://brands.home-assistant.io/${e.brand?"brands/":""}${e.useFallback?"_/":""}${e.domain}/${e.darkOptimized?"dark_":""}${e.type}.png`,a=e=>e.split("/")[4],o=e=>e.startsWith("https://brands.home-assistant.io/")}}]);
//# sourceMappingURL=2816.fbf095c7155fb4e6.js.map