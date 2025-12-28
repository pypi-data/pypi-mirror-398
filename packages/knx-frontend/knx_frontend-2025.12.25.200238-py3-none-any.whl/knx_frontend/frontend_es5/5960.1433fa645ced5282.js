"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["5960"],{81089:function(e,t,a){a.d(t,{n:function(){return n}});a(27495),a(25440);var n=e=>e.replace(/^_*(.)|_+(.)/g,((e,t,a)=>t?t.toUpperCase():" "+a.toUpperCase()))},17210:function(e,t,a){a.a(e,(async function(e,t){try{var n=a(3164),i=a(31432),o=a(78261),r=a(61397),s=a(50264),l=a(44734),c=a(56038),u=a(69683),h=a(6454),d=(a(28706),a(2008),a(74423),a(23792),a(62062),a(44114),a(18111),a(22489),a(7588),a(61701),a(36033),a(5506),a(26099),a(3362),a(23500),a(62953),a(62826)),p=a(96196),v=a(77845),f=a(92542),_=a(81089),m=a(80559),b=a(11129),g=a(55179),y=(a(94343),a(22598),e([g]));g=(y.then?(await y)():y)[0];var $,w,k,A,x=e=>e,I=[],M=e=>(0,p.qy)($||($=x`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${0} slot="start"></ha-icon>
    <span slot="headline">${0}</span>
    ${0}
  </ha-combo-box-item>
`),e.icon,e.title||e.path,e.title?(0,p.qy)(w||(w=x`<span slot="supporting-text">${0}</span>`),e.path):p.s6),C=(e,t,a)=>{var n,i,o;return{path:`/${e}/${null!==(n=t.path)&&void 0!==n?n:a}`,icon:null!==(i=t.icon)&&void 0!==i?i:"mdi:view-compact",title:null!==(o=t.title)&&void 0!==o?o:t.path?(0,_.n)(t.path):`${a}`}},Z=(e,t)=>({path:`/${t.url_path}`,icon:(0,b.Q)(t)||"mdi:view-dashboard",title:(0,b.hL)(e,t)||""}),q=function(e){function t(){var e;(0,l.A)(this,t);for(var a=arguments.length,n=new Array(a),i=0;i<a;i++)n[i]=arguments[i];return(e=(0,u.A)(this,t,[].concat(n))).disabled=!1,e.required=!1,e._opened=!1,e.navigationItemsLoaded=!1,e.navigationItems=I,e}return(0,h.A)(t,e),(0,c.A)(t,[{key:"render",value:function(){return(0,p.qy)(k||(k=x`
      <ha-combo-box
        .hass=${0}
        item-value-path="path"
        item-label-path="path"
        .value=${0}
        allow-custom-value
        .filteredItems=${0}
        .label=${0}
        .helper=${0}
        .disabled=${0}
        .required=${0}
        .renderer=${0}
        @opened-changed=${0}
        @value-changed=${0}
        @filter-changed=${0}
      >
      </ha-combo-box>
    `),this.hass,this._value,this.navigationItems,this.label,this.helper,this.disabled,this.required,M,this._openedChanged,this._valueChanged,this._filterChanged)}},{key:"_openedChanged",value:(d=(0,s.A)((0,r.A)().m((function e(t){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:this._opened=t.detail.value,this._opened&&!this.navigationItemsLoaded&&this._loadNavigationItems();case 1:return e.a(2)}}),e,this)}))),function(e){return d.apply(this,arguments)})},{key:"_loadNavigationItems",value:(a=(0,s.A)((0,r.A)().m((function e(){var t,a,s,l,c,u,h,d,p=this;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return this.navigationItemsLoaded=!0,t=Object.entries(this.hass.panels).map((e=>{var t=(0,o.A)(e,2),a=t[0],n=t[1];return Object.assign({id:a},n)})),a=t.filter((e=>"lovelace"===e.component_name)),e.n=1,Promise.all(a.map((e=>(0,m.Dz)(this.hass.connection,"lovelace"===e.url_path?null:e.url_path,!0).then((t=>[e.id,t])).catch((t=>[e.id,void 0])))));case 1:s=e.v,l=new Map(s),this.navigationItems=[],c=(0,i.A)(t),e.p=2,h=(0,r.A)().m((function e(){var t,a;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:if(t=u.value,p.navigationItems.push(Z(p.hass,t)),(a=l.get(t.id))&&"views"in a){e.n=1;break}return e.a(2,1);case 1:a.views.forEach(((e,a)=>p.navigationItems.push(C(t.url_path,e,a))));case 2:return e.a(2)}}),e)})),c.s();case 3:if((u=c.n()).done){e.n=6;break}return e.d((0,n.A)(h()),4);case 4:if(!e.v){e.n=5;break}return e.a(3,5);case 5:e.n=3;break;case 6:e.n=8;break;case 7:e.p=7,d=e.v,c.e(d);case 8:return e.p=8,c.f(),e.f(8);case 9:this.comboBox.filteredItems=this.navigationItems;case 10:return e.a(2)}}),e,this,[[2,7,8,9]])}))),function(){return a.apply(this,arguments)})},{key:"shouldUpdate",value:function(e){return!this._opened||e.has("_opened")}},{key:"_valueChanged",value:function(e){e.stopPropagation(),this._setValue(e.detail.value)}},{key:"_setValue",value:function(e){this.value=e,(0,f.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}},{key:"_filterChanged",value:function(e){var t=e.detail.value.toLowerCase();if(t.length>=2){var a=[];this.navigationItems.forEach((e=>{(e.path.toLowerCase().includes(t)||e.title.toLowerCase().includes(t))&&a.push(e)})),a.length>0?this.comboBox.filteredItems=a:this.comboBox.filteredItems=[]}else this.comboBox.filteredItems=this.navigationItems}},{key:"_value",get:function(){return this.value||""}}]);var a,d}(p.WF);q.styles=(0,p.AH)(A||(A=x`
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
  `)),(0,d.__decorate)([(0,v.MZ)({attribute:!1})],q.prototype,"hass",void 0),(0,d.__decorate)([(0,v.MZ)()],q.prototype,"label",void 0),(0,d.__decorate)([(0,v.MZ)()],q.prototype,"value",void 0),(0,d.__decorate)([(0,v.MZ)()],q.prototype,"helper",void 0),(0,d.__decorate)([(0,v.MZ)({type:Boolean})],q.prototype,"disabled",void 0),(0,d.__decorate)([(0,v.MZ)({type:Boolean})],q.prototype,"required",void 0),(0,d.__decorate)([(0,v.wk)()],q.prototype,"_opened",void 0),(0,d.__decorate)([(0,v.P)("ha-combo-box",!0)],q.prototype,"comboBox",void 0),q=(0,d.__decorate)([(0,v.EM)("ha-navigation-picker")],q),t()}catch(B){t(B)}}))},79691:function(e,t,a){a.a(e,(async function(e,n){try{a.r(t),a.d(t,{HaNavigationSelector:function(){return _}});var i=a(44734),o=a(56038),r=a(69683),s=a(6454),l=(a(28706),a(62826)),c=a(96196),u=a(77845),h=a(92542),d=a(17210),p=e([d]);d=(p.then?(await p)():p)[0];var v,f=e=>e,_=function(e){function t(){var e;(0,i.A)(this,t);for(var a=arguments.length,n=new Array(a),o=0;o<a;o++)n[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(n))).disabled=!1,e.required=!0,e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){return(0,c.qy)(v||(v=f`
      <ha-navigation-picker
        .hass=${0}
        .label=${0}
        .value=${0}
        .required=${0}
        .disabled=${0}
        .helper=${0}
        @value-changed=${0}
      ></ha-navigation-picker>
    `),this.hass,this.label,this.value,this.required,this.disabled,this.helper,this._valueChanged)}},{key:"_valueChanged",value:function(e){(0,h.r)(this,"value-changed",{value:e.detail.value})}}])}(c.WF);(0,l.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,l.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"selector",void 0),(0,l.__decorate)([(0,u.MZ)()],_.prototype,"value",void 0),(0,l.__decorate)([(0,u.MZ)()],_.prototype,"label",void 0),(0,l.__decorate)([(0,u.MZ)()],_.prototype,"helper",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean,reflect:!0})],_.prototype,"disabled",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],_.prototype,"required",void 0),_=(0,l.__decorate)([(0,u.EM)("ha-selector-navigation")],_),n()}catch(m){n(m)}}))},80559:function(e,t,a){a.d(t,{Dz:function(){return n}});var n=(e,t,a)=>e.sendMessagePromise({type:"lovelace/config",url_path:t,force:a})},11129:function(e,t,a){a.d(t,{Q:function(){return i},hL:function(){return n}});a(50113),a(18111),a(20116),a(26099),a(16034),a(58335);var n=(e,t)=>{var a=(e=>"lovelace"===e.url_path?"panel.states":"profile"===e.url_path?"panel.profile":`panel.${e.title}`)(t);return e.localize(a)||t.title||void 0},i=e=>{if(!e.icon)switch(e.component_name){case"profile":return"mdi:account";case"lovelace":return"mdi:view-dashboard"}return e.icon||void 0}},3164:function(e,t,a){a.d(t,{A:function(){return i}});a(52675),a(89463),a(16280),a(23792),a(26099),a(62953);var n=a(47075);function i(e){if(null!=e){var t=e["function"==typeof Symbol&&Symbol.iterator||"@@iterator"],a=0;if(t)return t.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length))return{next:function(){return e&&a>=e.length&&(e=void 0),{value:e&&e[a++],done:!e}}}}throw new TypeError((0,n.A)(e)+" is not iterable")}}}]);
//# sourceMappingURL=5960.1433fa645ced5282.js.map