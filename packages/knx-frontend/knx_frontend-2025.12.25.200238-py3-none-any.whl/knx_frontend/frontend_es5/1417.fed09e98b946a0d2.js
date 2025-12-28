"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["1417"],{45134:function(e,t,i){i.a(e,(async function(e,t){try{var r=i(94741),a=i(61397),s=i(50264),o=i(44734),n=i(56038),c=i(69683),l=i(6454),d=(i(28706),i(2008),i(74423),i(62062),i(18111),i(22489),i(61701),i(26099),i(62826)),u=i(96196),h=i(77845),v=i(92542),p=i(10085),_=i(53907),y=e([_]);_=(y.then?(await y)():y)[0];var b,f,A,k=e=>e,$=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,r=new Array(i),a=0;a<i;a++)r[a]=arguments[a];return(e=(0,c.A)(this,t,[].concat(r))).noAdd=!1,e.disabled=!1,e.required=!1,e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){if(!this.hass)return u.s6;var e=this._currentAreas;return(0,u.qy)(b||(b=k`
      ${0}
      <div>
        <ha-area-picker
          .noAdd=${0}
          .hass=${0}
          .label=${0}
          .helper=${0}
          .includeDomains=${0}
          .excludeDomains=${0}
          .includeDeviceClasses=${0}
          .deviceFilter=${0}
          .entityFilter=${0}
          .disabled=${0}
          .placeholder=${0}
          .required=${0}
          @value-changed=${0}
          .excludeAreas=${0}
        ></ha-area-picker>
      </div>
    `),e.map((e=>(0,u.qy)(f||(f=k`
          <div>
            <ha-area-picker
              .curValue=${0}
              .noAdd=${0}
              .hass=${0}
              .value=${0}
              .label=${0}
              .includeDomains=${0}
              .excludeDomains=${0}
              .includeDeviceClasses=${0}
              .deviceFilter=${0}
              .entityFilter=${0}
              .disabled=${0}
              @value-changed=${0}
            ></ha-area-picker>
          </div>
        `),e,this.noAdd,this.hass,e,this.pickedAreaLabel,this.includeDomains,this.excludeDomains,this.includeDeviceClasses,this.deviceFilter,this.entityFilter,this.disabled,this._areaChanged))),this.noAdd,this.hass,this.pickAreaLabel,this.helper,this.includeDomains,this.excludeDomains,this.includeDeviceClasses,this.deviceFilter,this.entityFilter,this.disabled,this.placeholder,this.required&&!e.length,this._addArea,e)}},{key:"_currentAreas",get:function(){return this.value||[]}},{key:"_updateAreas",value:(i=(0,s.A)((0,a.A)().m((function e(t){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:this.value=t,(0,v.r)(this,"value-changed",{value:t});case 1:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_areaChanged",value:function(e){e.stopPropagation();var t=e.currentTarget.curValue,i=e.detail.value;if(i!==t){var r=this._currentAreas;i&&!r.includes(i)?this._updateAreas(r.map((e=>e===t?i:e))):this._updateAreas(r.filter((e=>e!==t)))}}},{key:"_addArea",value:function(e){e.stopPropagation();var t=e.detail.value;if(t){e.currentTarget.value="";var i=this._currentAreas;i.includes(t)||this._updateAreas([].concat((0,r.A)(i),[t]))}}}]);var i}((0,p.E)(u.WF));$.styles=(0,u.AH)(A||(A=k`
    div {
      margin-top: 8px;
    }
  `)),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],$.prototype,"hass",void 0),(0,d.__decorate)([(0,h.MZ)()],$.prototype,"label",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array})],$.prototype,"value",void 0),(0,d.__decorate)([(0,h.MZ)()],$.prototype,"helper",void 0),(0,d.__decorate)([(0,h.MZ)()],$.prototype,"placeholder",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean,attribute:"no-add"})],$.prototype,"noAdd",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"include-domains"})],$.prototype,"includeDomains",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"exclude-domains"})],$.prototype,"excludeDomains",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"include-device-classes"})],$.prototype,"includeDeviceClasses",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],$.prototype,"deviceFilter",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],$.prototype,"entityFilter",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:"picked-area-label"})],$.prototype,"pickedAreaLabel",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:"pick-area-label"})],$.prototype,"pickAreaLabel",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean})],$.prototype,"disabled",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean})],$.prototype,"required",void 0),$=(0,d.__decorate)([(0,h.EM)("ha-areas-picker")],$),t()}catch(g){t(g)}}))},87888:function(e,t,i){i.a(e,(async function(e,r){try{i.r(t),i.d(t,{HaAreaSelector:function(){return M}});var a=i(44734),s=i(56038),o=i(69683),n=i(6454),c=(i(28706),i(18111),i(13579),i(26099),i(16034),i(62826)),l=i(96196),d=i(77845),u=i(22786),h=i(55376),v=i(1491),p=i(92542),_=i(28441),y=i(3950),b=i(82694),f=i(53907),A=i(45134),k=e([f,A]);[f,A]=k.then?(await k)():k;var $,g,m=e=>e,M=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,r=new Array(i),s=0;s<i;s++)r[s]=arguments[s];return(e=(0,o.A)(this,t,[].concat(r))).disabled=!1,e.required=!0,e._deviceIntegrationLookup=(0,u.A)(v.fk),e._filterEntities=t=>{var i;return null===(i=e.selector.area)||void 0===i||!i.entity||(0,h.e)(e.selector.area.entity).some((i=>(0,b.Ru)(i,t,e._entitySources)))},e._filterDevices=t=>{var i;if(null===(i=e.selector.area)||void 0===i||!i.device)return!0;var r=e._entitySources?e._deviceIntegrationLookup(e._entitySources,Object.values(e.hass.entities),Object.values(e.hass.devices),e._configEntries):void 0;return(0,h.e)(e.selector.area.device).some((e=>(0,b.vX)(e,t,r)))},e}return(0,n.A)(t,e),(0,s.A)(t,[{key:"_hasIntegration",value:function(e){var t,i;return(null===(t=e.area)||void 0===t?void 0:t.entity)&&(0,h.e)(e.area.entity).some((e=>e.integration))||(null===(i=e.area)||void 0===i?void 0:i.device)&&(0,h.e)(e.area.device).some((e=>e.integration))}},{key:"willUpdate",value:function(e){var t,i;e.get("selector")&&void 0!==this.value&&(null!==(t=this.selector.area)&&void 0!==t&&t.multiple&&!Array.isArray(this.value)?(this.value=[this.value],(0,p.r)(this,"value-changed",{value:this.value})):null!==(i=this.selector.area)&&void 0!==i&&i.multiple||!Array.isArray(this.value)||(this.value=this.value[0],(0,p.r)(this,"value-changed",{value:this.value})))}},{key:"updated",value:function(e){e.has("selector")&&this._hasIntegration(this.selector)&&!this._entitySources&&(0,_.c)(this.hass).then((e=>{this._entitySources=e})),!this._configEntries&&this._hasIntegration(this.selector)&&(this._configEntries=[],(0,y.VN)(this.hass).then((e=>{this._configEntries=e})))}},{key:"render",value:function(){var e,t,i,r,a;return this._hasIntegration(this.selector)&&!this._entitySources?l.s6:null!==(e=this.selector.area)&&void 0!==e&&e.multiple?(0,l.qy)(g||(g=m`
      <ha-areas-picker
        .hass=${0}
        .value=${0}
        .helper=${0}
        .pickAreaLabel=${0}
        no-add
        .deviceFilter=${0}
        .entityFilter=${0}
        .disabled=${0}
        .required=${0}
      ></ha-areas-picker>
    `),this.hass,this.value,this.helper,this.label,null!==(t=this.selector.area)&&void 0!==t&&t.device?this._filterDevices:void 0,null!==(i=this.selector.area)&&void 0!==i&&i.entity?this._filterEntities:void 0,this.disabled,this.required):(0,l.qy)($||($=m`
        <ha-area-picker
          .hass=${0}
          .value=${0}
          .label=${0}
          .helper=${0}
          no-add
          .deviceFilter=${0}
          .entityFilter=${0}
          .disabled=${0}
          .required=${0}
        ></ha-area-picker>
      `),this.hass,this.value,this.label,this.helper,null!==(r=this.selector.area)&&void 0!==r&&r.device?this._filterDevices:void 0,null!==(a=this.selector.area)&&void 0!==a&&a.entity?this._filterEntities:void 0,this.disabled,this.required)}}])}(l.WF);(0,c.__decorate)([(0,d.MZ)({attribute:!1})],M.prototype,"hass",void 0),(0,c.__decorate)([(0,d.MZ)({attribute:!1})],M.prototype,"selector",void 0),(0,c.__decorate)([(0,d.MZ)()],M.prototype,"value",void 0),(0,c.__decorate)([(0,d.MZ)()],M.prototype,"label",void 0),(0,c.__decorate)([(0,d.MZ)()],M.prototype,"helper",void 0),(0,c.__decorate)([(0,d.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,c.__decorate)([(0,d.MZ)({type:Boolean})],M.prototype,"required",void 0),(0,c.__decorate)([(0,d.wk)()],M.prototype,"_entitySources",void 0),(0,c.__decorate)([(0,d.wk)()],M.prototype,"_configEntries",void 0),M=(0,c.__decorate)([(0,d.EM)("ha-selector-area")],M),r()}catch(Z){r(Z)}}))},28441:function(e,t,i){i.d(t,{c:function(){return n}});var r=i(61397),a=i(50264),s=(i(28706),i(26099),i(3362),function(){var e=(0,a.A)((0,r.A)().m((function e(t,i,a,o,n){var c,l,d,u,h,v,p,_=arguments;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:for(c=_.length,l=new Array(c>5?c-5:0),d=5;d<c;d++)l[d-5]=_[d];if(h=(u=n)[t],v=e=>o&&o(n,e.result)!==e.cacheKey?(u[t]=void 0,s.apply(void 0,[t,i,a,o,n].concat(l))):e.result,!h){e.n=1;break}return e.a(2,h instanceof Promise?h.then(v):v(h));case 1:return p=a.apply(void 0,[n].concat(l)),u[t]=p,p.then((e=>{u[t]={result:e,cacheKey:null==o?void 0:o(n,e)},setTimeout((()=>{u[t]=void 0}),i)}),(()=>{u[t]=void 0})),e.a(2,p)}}),e)})));return function(t,i,r,a,s){return e.apply(this,arguments)}}()),o=e=>e.callWS({type:"entity/source"}),n=e=>s("_entitySources",3e4,o,(e=>Object.keys(e.states).length),e)},10085:function(e,t,i){i.d(t,{E:function(){return u}});var r=i(31432),a=i(44734),s=i(56038),o=i(69683),n=i(25460),c=i(6454),l=(i(74423),i(23792),i(18111),i(13579),i(26099),i(3362),i(62953),i(62826)),d=i(77845),u=e=>{var t=function(e){function t(){return(0,a.A)(this,t),(0,o.A)(this,t,arguments)}return(0,c.A)(t,e),(0,s.A)(t,[{key:"connectedCallback",value:function(){(0,n.A)(t,"connectedCallback",this,3)([]),this._checkSubscribed()}},{key:"disconnectedCallback",value:function(){if((0,n.A)(t,"disconnectedCallback",this,3)([]),this.__unsubs){for(;this.__unsubs.length;){var e=this.__unsubs.pop();e instanceof Promise?e.then((e=>e())):e()}this.__unsubs=void 0}}},{key:"updated",value:function(e){if((0,n.A)(t,"updated",this,3)([e]),e.has("hass"))this._checkSubscribed();else if(this.hassSubscribeRequiredHostProps){var i,a=(0,r.A)(e.keys());try{for(a.s();!(i=a.n()).done;){var s=i.value;if(this.hassSubscribeRequiredHostProps.includes(s))return void this._checkSubscribed()}}catch(o){a.e(o)}finally{a.f()}}}},{key:"hassSubscribe",value:function(){return[]}},{key:"_checkSubscribed",value:function(){var e;void 0!==this.__unsubs||!this.isConnected||void 0===this.hass||null!==(e=this.hassSubscribeRequiredHostProps)&&void 0!==e&&e.some((e=>void 0===this[e]))||(this.__unsubs=this.hassSubscribe())}}])}(e);return(0,l.__decorate)([(0,d.MZ)({attribute:!1})],t.prototype,"hass",void 0),t}}}]);
//# sourceMappingURL=1417.fed09e98b946a0d2.js.map