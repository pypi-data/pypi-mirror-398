export const __webpack_id__="2401";export const __webpack_ids__=["2401"];export const __webpack_modules__={39623:function(e,t,r){r.a(e,(async function(e,a){try{r.r(t),r.d(t,{HaLabelSelector:()=>u});var o=r(62826),s=r(96196),i=r(77845),l=r(55376),n=r(92542),d=r(32649),c=e([d]);d=(c.then?(await c)():c)[0];class u extends s.WF{render(){return this.selector.label.multiple?s.qy`
        <ha-labels-picker
          no-add
          .hass=${this.hass}
          .value=${(0,l.e)(this.value??[])}
          .required=${this.required}
          .disabled=${this.disabled}
          .label=${this.label}
          @value-changed=${this._handleChange}
        >
        </ha-labels-picker>
      `:s.qy`
      <ha-label-picker
        no-add
        .hass=${this.hass}
        .value=${this.value}
        .required=${this.required}
        .disabled=${this.disabled}
        .label=${this.label}
        @value-changed=${this._handleChange}
      >
      </ha-label-picker>
    `}_handleChange(e){let t=e.detail.value;this.value!==t&&((""===t||Array.isArray(t)&&0===t.length)&&!this.required&&(t=void 0),(0,n.r)(this,"value-changed",{value:t}))}constructor(...e){super(...e),this.disabled=!1,this.required=!0}}u.styles=s.AH`
    ha-labels-picker {
      display: block;
      width: 100%;
    }
  `,(0,o.__decorate)([(0,i.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,o.__decorate)([(0,i.MZ)()],u.prototype,"value",void 0),(0,o.__decorate)([(0,i.MZ)()],u.prototype,"name",void 0),(0,o.__decorate)([(0,i.MZ)()],u.prototype,"label",void 0),(0,o.__decorate)([(0,i.MZ)()],u.prototype,"placeholder",void 0),(0,o.__decorate)([(0,i.MZ)()],u.prototype,"helper",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],u.prototype,"selector",void 0),(0,o.__decorate)([(0,i.MZ)({type:Boolean})],u.prototype,"disabled",void 0),(0,o.__decorate)([(0,i.MZ)({type:Boolean})],u.prototype,"required",void 0),u=(0,o.__decorate)([(0,i.EM)("ha-selector-label")],u),a()}catch(u){a(u)}}))},70570:function(e,t,r){r.d(t,{N:()=>s});const a=e=>{let t=[];function r(r,a){e=a?r:Object.assign(Object.assign({},e),r);let o=t;for(let t=0;t<o.length;t++)o[t](e)}return{get state(){return e},action(t){function a(e){r(e,!1)}return function(){let r=[e];for(let e=0;e<arguments.length;e++)r.push(arguments[e]);let o=t.apply(this,r);if(null!=o)return o instanceof Promise?o.then(a):a(o)}},setState:r,clearState(){e=void 0},subscribe(e){return t.push(e),()=>{!function(e){let r=[];for(let a=0;a<t.length;a++)t[a]===e?e=null:r.push(t[a]);t=r}(e)}}}},o=(e,t,r,o,s={unsubGrace:!0})=>{if(e[t])return e[t];let i,l,n=0,d=a();const c=()=>{if(!r)throw new Error("Collection does not support refresh");return r(e).then((e=>d.setState(e,!0)))},u=()=>c().catch((t=>{if(e.connected)throw t})),h=()=>{l=void 0,i&&i.then((e=>{e()})),d.clearState(),e.removeEventListener("ready",c),e.removeEventListener("disconnected",p)},p=()=>{l&&(clearTimeout(l),h())};return e[t]={get state(){return d.state},refresh:c,subscribe(t){n++,1===n&&(()=>{if(void 0!==l)return clearTimeout(l),void(l=void 0);o&&(i=o(e,d)),r&&(e.addEventListener("ready",u),u()),e.addEventListener("disconnected",p)})();const a=d.subscribe(t);return void 0!==d.state&&setTimeout((()=>t(d.state)),0),()=>{a(),n--,n||(s.unsubGrace?l=setTimeout(h,5e3):h())}}},e[t]},s=(e,t,r,a,s)=>o(a,e,t,r).subscribe(s)}};
//# sourceMappingURL=2401.c500225927e3e619.js.map