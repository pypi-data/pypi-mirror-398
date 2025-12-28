"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["624"],{88867:function(e,t,r){r.a(e,(async function(e,n){try{r.r(t),r.d(t,{HaIconPicker:function(){return I}});var o=r(31432),a=r(44734),i=r(56038),s=r(69683),c=r(6454),l=r(61397),u=r(94741),d=r(50264),h=(r(28706),r(2008),r(74423),r(23792),r(62062),r(44114),r(34782),r(26910),r(18111),r(22489),r(7588),r(61701),r(13579),r(26099),r(3362),r(31415),r(17642),r(58004),r(33853),r(45876),r(32475),r(15024),r(31698),r(23500),r(62953),r(62826)),p=r(96196),v=r(77845),f=r(22786),y=r(92542),_=r(33978),b=r(55179),m=(r(22598),r(94343),e([b]));b=(m.then?(await m)():m)[0];var k,g,w,$,A,M=e=>e,x=[],q=!1,Z=function(){var e=(0,d.A)((0,l.A)().m((function e(){var t,n;return(0,l.A)().w((function(e){for(;;)switch(e.n){case 0:return q=!0,e.n=1,r.e("3451").then(r.t.bind(r,83174,19));case 1:return t=e.v,x=t.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords}))),n=[],Object.keys(_.y).forEach((e=>{n.push(C(e))})),e.n=2,Promise.all(n);case 2:e.v.forEach((e=>{var t;(t=x).push.apply(t,(0,u.A)(e))}));case 3:return e.a(2)}}),e)})));return function(){return e.apply(this,arguments)}}(),C=function(){var e=(0,d.A)((0,l.A)().m((function e(t){var r,n,o;return(0,l.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(e.p=0,"function"==typeof(r=_.y[t].getIconList)){e.n=1;break}return e.a(2,[]);case 1:return e.n=2,r();case 2:return n=e.v,o=n.map((e=>{var r;return{icon:`${t}:${e.name}`,parts:new Set(e.name.split("-")),keywords:null!==(r=e.keywords)&&void 0!==r?r:[]}})),e.a(2,o);case 3:return e.p=3,e.v,console.warn(`Unable to load icon list for ${t} iconset`),e.a(2,[])}}),e,null,[[0,3]])})));return function(t){return e.apply(this,arguments)}}(),P=e=>(0,p.qy)(k||(k=M`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${0} slot="start"></ha-icon>
    ${0}
  </ha-combo-box-item>
`),e.icon,e.icon),I=function(e){function t(){var e;(0,a.A)(this,t);for(var r=arguments.length,n=new Array(r),i=0;i<r;i++)n[i]=arguments[i];return(e=(0,s.A)(this,t,[].concat(n))).disabled=!1,e.required=!1,e.invalid=!1,e._filterIcons=(0,f.A)((function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:x;if(!e)return t;var r,n=[],a=(e,t)=>n.push({icon:e,rank:t}),i=(0,o.A)(t);try{for(i.s();!(r=i.n()).done;){var s=r.value;s.parts.has(e)?a(s.icon,1):s.keywords.includes(e)?a(s.icon,2):s.icon.includes(e)?a(s.icon,3):s.keywords.some((t=>t.includes(e)))&&a(s.icon,4)}}catch(c){i.e(c)}finally{i.f()}return 0===n.length&&a(e,0),n.sort(((e,t)=>e.rank-t.rank))})),e._iconProvider=(t,r)=>{var n=e._filterIcons(t.filter.toLowerCase(),x),o=t.page*t.pageSize,a=o+t.pageSize;r(n.slice(o,a),n.length)},e}return(0,c.A)(t,e),(0,i.A)(t,[{key:"render",value:function(){return(0,p.qy)(g||(g=M`
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
    `),this.hass,this._value,q?this._iconProvider:void 0,this.label,this.helper,this.disabled,this.required,this.placeholder,this.errorMessage,this.invalid,P,this._openedChanged,this._valueChanged,this._value||this.placeholder?(0,p.qy)(w||(w=M`
              <ha-icon .icon=${0} slot="icon">
              </ha-icon>
            `),this._value||this.placeholder):(0,p.qy)($||($=M`<slot slot="icon" name="fallback"></slot>`)))}},{key:"_openedChanged",value:(r=(0,d.A)((0,l.A)().m((function e(t){return(0,l.A)().w((function(e){for(;;)switch(e.n){case 0:if(!t.detail.value||q){e.n=2;break}return e.n=1,Z();case 1:this.requestUpdate();case 2:return e.a(2)}}),e,this)}))),function(e){return r.apply(this,arguments)})},{key:"_valueChanged",value:function(e){e.stopPropagation(),this._setValue(e.detail.value)}},{key:"_setValue",value:function(e){this.value=e,(0,y.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}},{key:"_value",get:function(){return this.value||""}}]);var r}(p.WF);I.styles=(0,p.AH)(A||(A=M`
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
  `)),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],I.prototype,"hass",void 0),(0,h.__decorate)([(0,v.MZ)()],I.prototype,"value",void 0),(0,h.__decorate)([(0,v.MZ)()],I.prototype,"label",void 0),(0,h.__decorate)([(0,v.MZ)()],I.prototype,"helper",void 0),(0,h.__decorate)([(0,v.MZ)()],I.prototype,"placeholder",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:"error-message"})],I.prototype,"errorMessage",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],I.prototype,"disabled",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],I.prototype,"required",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],I.prototype,"invalid",void 0),I=(0,h.__decorate)([(0,v.EM)("ha-icon-picker")],I),n()}catch(S){n(S)}}))}}]);
//# sourceMappingURL=624.d073dd2fa9d41d56.js.map