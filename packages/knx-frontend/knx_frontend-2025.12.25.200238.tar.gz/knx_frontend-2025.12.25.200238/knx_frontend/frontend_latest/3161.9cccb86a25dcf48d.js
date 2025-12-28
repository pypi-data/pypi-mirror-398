export const __webpack_id__="3161";export const __webpack_ids__=["3161"];export const __webpack_modules__={10393:function(e,t,i){i.d(t,{M:()=>a,l:()=>s});const s=new Set(["primary","accent","disabled","red","pink","purple","deep-purple","indigo","blue","light-blue","cyan","teal","green","light-green","lime","yellow","amber","orange","deep-orange","brown","light-grey","grey","dark-grey","blue-grey","black","white"]);function a(e){return s.has(e)?`var(--${e}-color)`:e}},87328:function(e,t,i){i.d(t,{aH:()=>o});var s=i(16727),a=i(91889);const r=[" ",": "," - "],n=e=>e.toLowerCase()!==e,o=(e,t,i)=>{const s=t[e.entity_id];return s?c(s,i):(0,a.u)(e)},c=(e,t,i)=>{const o=e.name||("original_name"in e&&null!=e.original_name?String(e.original_name):void 0),c=e.device_id?t[e.device_id]:void 0;if(!c)return o||(i?(0,a.u)(i):void 0);const d=(0,s.xn)(c);return d!==o?d&&o&&((e,t)=>{const i=e.toLowerCase(),s=t.toLowerCase();for(const a of r){const t=`${s}${a}`;if(i.startsWith(t)){const i=e.substring(t.length);if(i.length)return n(i.substr(0,i.indexOf(" ")))?i:i[0].toUpperCase()+i.slice(1)}}})(o,d)||o:void 0}},79384:function(e,t,i){i.d(t,{Cf:()=>c});var s=i(56403),a=i(16727),r=i(87328),n=i(47644),o=i(87400);const c=(e,t,i,c,d,h)=>{const{device:l,area:p,floor:u}=(0,o.l)(e,i,c,d,h);return t.map((t=>{switch(t.type){case"entity":return(0,r.aH)(e,i,c);case"device":return l?(0,a.xn)(l):void 0;case"area":return p?(0,s.A)(p):void 0;case"floor":return u?(0,n.X)(u):void 0;case"text":return t.text;default:return""}}))}},87400:function(e,t,i){i.d(t,{l:()=>s});const s=(e,t,i,s,r)=>{const n=t[e.entity_id];return n?a(n,t,i,s,r):{entity:null,device:null,area:null,floor:null}},a=(e,t,i,s,a)=>{const r=t[e.entity_id],n=e?.device_id,o=n?i[n]:void 0,c=e?.area_id||o?.area_id,d=c?s[c]:void 0,h=d?.floor_id;return{entity:r,device:o||null,area:d||null,floor:(h?a[h]:void 0)||null}}},45996:function(e,t,i){i.d(t,{n:()=>a});const s=/^(\w+)\.(\w+)$/,a=e=>s.test(e)},93777:function(e,t,i){i.d(t,{Y:()=>s});const s=(e,t="_")=>{const i="àáâäæãåāăąабçćčđďдèéêëēėęěеёэфğǵгḧхîïíīįìıİийкłлḿмñńǹňнôöòóœøōõőоṕпŕřрßśšşșсťțтûüùúūǘůűųувẃẍÿýыžźżз·",s=`aaaaaaaaaaabcccdddeeeeeeeeeeefggghhiiiiiiiiijkllmmnnnnnoooooooooopprrrsssssstttuuuuuuuuuuvwxyyyzzzz${t}`,a=new RegExp(i.split("").join("|"),"g"),r={"ж":"zh","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"shch","ю":"iu","я":"ia"};let n;return""===e?n="":(n=e.toString().toLowerCase().replace(a,(e=>s.charAt(i.indexOf(e)))).replace(/[а-я]/g,(e=>r[e]||"")).replace(/(\d),(?=\d)/g,"$1").replace(/[^a-z0-9]+/g,t).replace(new RegExp(`(${t})\\1+`,"g"),"$1").replace(new RegExp(`^${t}+`),"").replace(new RegExp(`${t}+$`),""),""===n&&(n="unknown")),n}},17504:function(e,t,i){i.a(e,(async function(e,s){try{i.r(t),i.d(t,{HaTargetSelector:()=>_});var a=i(62826),r=i(96196),n=i(77845),o=i(22786),c=i(55376),d=i(1491),h=i(28441),l=i(82694),p=i(58523),u=e([p]);p=(u.then?(await u)():u)[0];class _ extends r.WF{_hasIntegration(e){return e.target?.entity&&(0,c.e)(e.target.entity).some((e=>e.integration))||e.target?.device&&(0,c.e)(e.target.device).some((e=>e.integration))}updated(e){super.updated(e),e.has("selector")&&this._hasIntegration(this.selector)&&!this._entitySources&&(0,h.c)(this.hass).then((e=>{this._entitySources=e})),e.has("selector")&&(this._createDomains=(0,l.Lo)(this.selector))}render(){return this._hasIntegration(this.selector)&&!this._entitySources?r.s6:r.qy` ${this.label?r.qy`<label>${this.label}</label>`:r.s6}
      <ha-target-picker
        .hass=${this.hass}
        .value=${this.value}
        .helper=${this.helper}
        .deviceFilter=${this._filterDevices}
        .entityFilter=${this._filterEntities}
        .disabled=${this.disabled}
        .createDomains=${this._createDomains}
      ></ha-target-picker>`}constructor(...e){super(...e),this.disabled=!1,this._deviceIntegrationLookup=(0,o.A)(d.fk),this._filterEntities=e=>!this.selector.target?.entity||(0,c.e)(this.selector.target.entity).some((t=>(0,l.Ru)(t,e,this._entitySources))),this._filterDevices=e=>{if(!this.selector.target?.device)return!0;const t=this._entitySources?this._deviceIntegrationLookup(this._entitySources,Object.values(this.hass.entities)):void 0;return(0,c.e)(this.selector.target.device).some((i=>(0,l.vX)(i,e,t)))}}}_.styles=r.AH`
    ha-target-picker {
      display: block;
    }
  `,(0,a.__decorate)([(0,n.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,a.__decorate)([(0,n.MZ)({attribute:!1})],_.prototype,"selector",void 0),(0,a.__decorate)([(0,n.MZ)({type:Object})],_.prototype,"value",void 0),(0,a.__decorate)([(0,n.MZ)()],_.prototype,"label",void 0),(0,a.__decorate)([(0,n.MZ)()],_.prototype,"helper",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,a.__decorate)([(0,n.wk)()],_.prototype,"_entitySources",void 0),(0,a.__decorate)([(0,n.wk)()],_.prototype,"_createDomains",void 0),_=(0,a.__decorate)([(0,n.EM)("ha-selector-target")],_),s()}catch(_){s(_)}}))},4148:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),a=i(96196),r=i(77845),n=i(3890),o=i(97382),c=i(43197),d=(i(22598),i(60961),e([c]));c=(d.then?(await d)():d)[0];class h extends a.WF{render(){const e=this.icon||this.stateObj&&this.hass?.entities[this.stateObj.entity_id]?.icon||this.stateObj?.attributes.icon;if(e)return a.qy`<ha-icon .icon=${e}></ha-icon>`;if(!this.stateObj)return a.s6;if(!this.hass)return this._renderFallback();const t=(0,c.fq)(this.hass,this.stateObj,this.stateValue).then((e=>e?a.qy`<ha-icon .icon=${e}></ha-icon>`:this._renderFallback()));return a.qy`${(0,n.T)(t)}`}_renderFallback(){const e=(0,o.t)(this.stateObj);return a.qy`
      <ha-svg-icon
        .path=${c.l[e]||c.lW}
      ></ha-svg-icon>
    `}}(0,s.__decorate)([(0,r.MZ)({attribute:!1})],h.prototype,"hass",void 0),(0,s.__decorate)([(0,r.MZ)({attribute:!1})],h.prototype,"stateObj",void 0),(0,s.__decorate)([(0,r.MZ)({attribute:!1})],h.prototype,"stateValue",void 0),(0,s.__decorate)([(0,r.MZ)()],h.prototype,"icon",void 0),h=(0,s.__decorate)([(0,r.EM)("ha-state-icon")],h),t()}catch(h){t(h)}}))},58523:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),a=i(61366),r=i(16527),n=i(94454),o=i(78648),c=i(96196),d=i(77845),h=i(29485),l=i(22786),p=i(55376),u=i(92542),_=i(45996),m=i(79599),y=i(45494),v=i(3950),g=i(34972),b=i(1491),f=i(22800),$=i(84125),x=i(41327),k=i(6098),w=i(10085),M=i(50218),I=i(64070),C=i(69847),D=i(76681),L=i(96943),q=(i(60961),i(31009),i(31532)),F=i(60019),H=e([a,L,q,F]);[a,L,q,F]=H.then?(await H)():H;const z="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",V="M20 2H4C2.9 2 2 2.9 2 4V20C2 21.11 2.9 22 4 22H20C21.11 22 22 21.11 22 20V4C22 2.9 21.11 2 20 2M4 6L6 4H10.9L4 10.9V6M4 13.7L13.7 4H18.6L4 18.6V13.7M20 18L18 20H13.1L20 13.1V18M20 10.3L10.3 20H5.4L20 5.4V10.3Z",E="________",Z="___create-new-entity___";class O extends((0,w.E)(c.WF)){get _showEntityId(){return this.hass.userData?.showEntityIdPicker}willUpdate(e){super.willUpdate(e),this.hasUpdated||this._loadConfigEntries()}render(){return this.addOnTop?c.qy` ${this._renderPicker()} ${this._renderItems()} `:c.qy` ${this._renderItems()} ${this._renderPicker()} `}_renderValueChips(){const e=this.value?.entity_id?(0,p.e)(this.value.entity_id):[],t=this.value?.device_id?(0,p.e)(this.value.device_id):[],i=this.value?.area_id?(0,p.e)(this.value.area_id):[],s=this.value?.floor_id?(0,p.e)(this.value.floor_id):[],a=this.value?.label_id?(0,p.e)(this.value.label_id):[];return e.length||t.length||i.length||s.length||a.length?c.qy`
      <div class="mdc-chip-set items">
        ${s.length?s.map((e=>c.qy`
                <ha-target-picker-value-chip
                  .hass=${this.hass}
                  type="floor"
                  .itemId=${e}
                  @remove-target-item=${this._handleRemove}
                  @expand-target-item=${this._handleExpand}
                ></ha-target-picker-value-chip>
              `)):c.s6}
        ${i.length?i.map((e=>c.qy`
                <ha-target-picker-value-chip
                  .hass=${this.hass}
                  type="area"
                  .itemId=${e}
                  @remove-target-item=${this._handleRemove}
                  @expand-target-item=${this._handleExpand}
                ></ha-target-picker-value-chip>
              `)):c.s6}
        ${t.length?t.map((e=>c.qy`
                <ha-target-picker-value-chip
                  .hass=${this.hass}
                  type="device"
                  .itemId=${e}
                  @remove-target-item=${this._handleRemove}
                  @expand-target-item=${this._handleExpand}
                ></ha-target-picker-value-chip>
              `)):c.s6}
        ${e.length?e.map((e=>c.qy`
                <ha-target-picker-value-chip
                  .hass=${this.hass}
                  type="entity"
                  .itemId=${e}
                  @remove-target-item=${this._handleRemove}
                  @expand-target-item=${this._handleExpand}
                ></ha-target-picker-value-chip>
              `)):c.s6}
        ${a.length?a.map((e=>c.qy`
                <ha-target-picker-value-chip
                  .hass=${this.hass}
                  type="label"
                  .itemId=${e}
                  @remove-target-item=${this._handleRemove}
                  @expand-target-item=${this._handleExpand}
                ></ha-target-picker-value-chip>
              `)):c.s6}
      </div>
    `:c.s6}_renderValueGroups(){const e=this.value?.entity_id?(0,p.e)(this.value.entity_id):[],t=this.value?.device_id?(0,p.e)(this.value.device_id):[],i=this.value?.area_id?(0,p.e)(this.value.area_id):[],s=this.value?.floor_id?(0,p.e)(this.value.floor_id):[],a=this.value?.label_id?(0,p.e)(this.value?.label_id):[];return e.length||t.length||i.length||s.length||a.length?c.qy`
      <div class="item-groups">
        ${e.length?c.qy`
              <ha-target-picker-item-group
                @remove-target-item=${this._handleRemove}
                type="entity"
                .hass=${this.hass}
                .items=${{entity:e}}
                .deviceFilter=${this.deviceFilter}
                .entityFilter=${this.entityFilter}
                .includeDomains=${this.includeDomains}
                .includeDeviceClasses=${this.includeDeviceClasses}
              >
              </ha-target-picker-item-group>
            `:c.s6}
        ${t.length?c.qy`
              <ha-target-picker-item-group
                @remove-target-item=${this._handleRemove}
                type="device"
                .hass=${this.hass}
                .items=${{device:t}}
                .deviceFilter=${this.deviceFilter}
                .entityFilter=${this.entityFilter}
                .includeDomains=${this.includeDomains}
                .includeDeviceClasses=${this.includeDeviceClasses}
              >
              </ha-target-picker-item-group>
            `:c.s6}
        ${s.length||i.length?c.qy`
              <ha-target-picker-item-group
                @remove-target-item=${this._handleRemove}
                type="area"
                .hass=${this.hass}
                .items=${{floor:s,area:i}}
                .deviceFilter=${this.deviceFilter}
                .entityFilter=${this.entityFilter}
                .includeDomains=${this.includeDomains}
                .includeDeviceClasses=${this.includeDeviceClasses}
              >
              </ha-target-picker-item-group>
            `:c.s6}
        ${a.length?c.qy`
              <ha-target-picker-item-group
                @remove-target-item=${this._handleRemove}
                type="label"
                .hass=${this.hass}
                .items=${{label:a}}
                .deviceFilter=${this.deviceFilter}
                .entityFilter=${this.entityFilter}
                .includeDomains=${this.includeDomains}
                .includeDeviceClasses=${this.includeDeviceClasses}
              >
              </ha-target-picker-item-group>
            `:c.s6}
      </div>
    `:c.s6}_renderItems(){return c.qy`
      ${this.compact?this._renderValueChips():this._renderValueGroups()}
    `}_renderPicker(){const e=[{id:"entity",label:this.hass.localize("ui.components.target-picker.type.entities")},{id:"device",label:this.hass.localize("ui.components.target-picker.type.devices")},{id:"area",label:this.hass.localize("ui.components.target-picker.type.areas")},"separator",{id:"label",label:this.hass.localize("ui.components.target-picker.type.labels")}];return c.qy`
      <div class="add-target-wrapper">
        <ha-generic-picker
          .hass=${this.hass}
          .disabled=${this.disabled}
          .autofocus=${this.autofocus}
          .helper=${this.helper}
          .sections=${e}
          .notFoundLabel=${this._noTargetFoundLabel}
          .emptyLabel=${this.hass.localize("ui.components.target-picker.no_targets")}
          .sectionTitleFunction=${this._sectionTitleFunction}
          .selectedSection=${this._selectedSection}
          .rowRenderer=${this._renderRow}
          .getItems=${this._getItems}
          @value-changed=${this._targetPicked}
          .addButtonLabel=${this.hass.localize("ui.components.target-picker.add_target")}
          .getAdditionalItems=${this._getAdditionalItems}
        >
        </ha-generic-picker>
      </div>
    `}_targetPicked(e){e.stopPropagation();const t=e.detail.value;if(t.startsWith(Z))return void this._createNewDomainElement(t.substring(Z.length));const[i,s]=e.detail.value.split(E);this._addTarget(s,i)}_addTarget(e,t){const i=`${t}_id`;("entity_id"!==i||(0,_.n)(e))&&(this.value&&this.value[i]&&(0,p.e)(this.value[i]).includes(e)||((0,u.r)(this,"value-changed",{value:this.value?{...this.value,[i]:this.value[i]?[...(0,p.e)(this.value[i]),e]:e}:{[i]:e}}),this.shadowRoot?.querySelector(`ha-target-picker-item-group[type='${this._newTarget?.type}']`)?.removeAttribute("collapsed")))}_handleRemove(e){const{type:t,id:i}=e.detail;(0,u.r)(this,"value-changed",{value:this._removeItem(this.value,t,i)})}_handleExpand(e){const t=e.detail.type,i=e.detail.id,s=[],a=[],r=[];if("floor"===t)Object.values(this.hass.areas).forEach((e=>{e.floor_id===i&&!this.value.area_id?.includes(e.area_id)&&(0,k.Kx)(e,this.hass.devices,this.hass.entities,this.deviceFilter,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter)&&s.push(e.area_id)}));else if("area"===t)Object.values(this.hass.devices).forEach((e=>{e.area_id===i&&!this.value.device_id?.includes(e.id)&&(0,k.Ly)(e,this.hass.entities,this.deviceFilter,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter)&&a.push(e.id)})),Object.values(this.hass.entities).forEach((e=>{e.area_id===i&&!this.value.entity_id?.includes(e.entity_id)&&(0,k.YK)(e,!1,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter)&&r.push(e.entity_id)}));else if("device"===t)Object.values(this.hass.entities).forEach((e=>{e.device_id===i&&!this.value.entity_id?.includes(e.entity_id)&&(0,k.YK)(e,!1,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter)&&r.push(e.entity_id)}));else{if("label"!==t)return;Object.values(this.hass.areas).forEach((e=>{e.labels.includes(i)&&!this.value.area_id?.includes(e.area_id)&&(0,k.Kx)(e,this.hass.devices,this.hass.entities,this.deviceFilter,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter)&&s.push(e.area_id)})),Object.values(this.hass.devices).forEach((e=>{e.labels.includes(i)&&!this.value.device_id?.includes(e.id)&&(0,k.Ly)(e,this.hass.entities,this.deviceFilter,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter)&&a.push(e.id)})),Object.values(this.hass.entities).forEach((e=>{e.labels.includes(i)&&!this.value.entity_id?.includes(e.entity_id)&&(0,k.YK)(e,!0,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter)&&r.push(e.entity_id)}))}let n=this.value;r.length&&(n=this._addItems(n,"entity_id",r)),a.length&&(n=this._addItems(n,"device_id",a)),s.length&&(n=this._addItems(n,"area_id",s)),n=this._removeItem(n,t,i),(0,u.r)(this,"value-changed",{value:n})}_addItems(e,t,i){return{...e,[t]:e[t]?(0,p.e)(e[t]).concat(i):i}}_removeItem(e,t,i){const s=`${t}_id`,a=(0,p.e)(e[s]).filter((e=>String(e)!==i));if(a.length)return{...e,[s]:a};const r={...e};return delete r[s],Object.keys(r).length?r:void 0}_filterGroup(e,t,i,s){const a=this._fuseIndexes[e](t),r=new C.b(t,{shouldSort:!1,minMatchCharLength:Math.min(i.length,2)},a).multiTermsSearch(i);let n=t;if(r&&(n=r.map((e=>e.item))),!s)return n;const o=n.findIndex((e=>s(e)));if(-1===o)return n;const[c]=n.splice(o,1);return n.unshift(c),n}async _loadConfigEntries(){const e=await(0,v.VN)(this.hass);this._configEntryLookup=Object.fromEntries(e.map((e=>[e.entry_id,e])))}static get styles(){return c.AH`
      .add-target-wrapper {
        display: flex;
        justify-content: flex-start;
        margin-top: var(--ha-space-3);
      }

      ha-generic-picker {
        width: 100%;
      }

      ${(0,c.iz)(n)}
      .items {
        z-index: 2;
      }
      .mdc-chip-set {
        padding: var(--ha-space-1) var(--ha-space-0);
        gap: var(--ha-space-2);
      }

      .item-groups {
        overflow: hidden;
        border: 2px solid var(--divider-color);
        border-radius: var(--ha-border-radius-lg);
      }
    `}constructor(...e){super(...e),this.compact=!1,this.disabled=!1,this.addOnTop=!1,this._configEntryLookup={},this._getDevicesMemoized=(0,l.A)(b.oG),this._getLabelsMemoized=(0,l.A)(x.IV),this._getEntitiesMemoized=(0,l.A)(f.wz),this._getAreasAndFloorsMemoized=(0,l.A)(y.b),this._fuseIndexes={area:(0,l.A)((e=>this._createFuseIndex(e))),entity:(0,l.A)((e=>this._createFuseIndex(e))),device:(0,l.A)((e=>this._createFuseIndex(e))),label:(0,l.A)((e=>this._createFuseIndex(e)))},this._createFuseIndex=e=>o.A.createIndex(["search_labels"],e),this._createNewDomainElement=e=>{(0,I.$)(this,{domain:e,dialogClosedCallback:e=>{e.entityId&&requestAnimationFrame((()=>{this._addTarget(e.entityId,"entity")}))}})},this._sectionTitleFunction=({firstIndex:e,lastIndex:t,firstItem:i,secondItem:s,itemsCount:a})=>{if(void 0===i||void 0===s||"string"==typeof i||"string"==typeof s&&"padding"!==s||0===e&&t===a-1)return;const r=(0,k.OJ)(i),n="area"===r||"floor"===r?"areas":"entity"===r?"entities":r&&"empty"!==r?`${r}s`:void 0;return n?this.hass.localize(`ui.components.target-picker.type.${n}`):void 0},this._getItems=(e,t)=>(this._selectedSection=t,this._getItemsMemoized(this.hass.localize,this.entityFilter,this.deviceFilter,this.includeDomains,this.includeDeviceClasses,this.value,e,this._configEntryLookup,this._selectedSection)),this._getItemsMemoized=(0,l.A)(((e,t,i,s,a,r,n,o,c)=>{const d=[];if(!c||"entity"===c){let i=this._getEntitiesMemoized(this.hass,s,void 0,t,a,void 0,void 0,r?.entity_id?(0,p.e)(r.entity_id):void 0,void 0,`entity${E}`);n&&(i=this._filterGroup("entity",i,n,(e=>e.stateObj?.entity_id===n))),!c&&i.length&&d.push(e("ui.components.target-picker.type.entities")),d.push(...i)}if(!c||"device"===c){let h=this._getDevicesMemoized(this.hass,o,s,void 0,a,i,t,r?.device_id?(0,p.e)(r.device_id):void 0,void 0,`device${E}`);n&&(h=this._filterGroup("device",h,n)),!c&&h.length&&d.push(e("ui.components.target-picker.type.devices")),d.push(...h)}if(!c||"area"===c){let o=this._getAreasAndFloorsMemoized(this.hass.states,this.hass.floors,this.hass.areas,this.hass.devices,this.hass.entities,(0,l.A)((e=>[e.type,e.id].join(E))),s,void 0,a,i,t,r?.area_id?(0,p.e)(r.area_id):void 0,r?.floor_id?(0,p.e)(r.floor_id):void 0);n&&(o=this._filterGroup("area",o,n)),!c&&o.length&&d.push(e("ui.components.target-picker.type.areas")),d.push(...o.map(((e,t)=>{const i=o[t+1];return!i||"area"===e.type&&"floor"===i.type?{...e,last:!0}:e})))}if(!c||"label"===c){let o=this._getLabelsMemoized(this.hass.states,this.hass.areas,this.hass.devices,this.hass.entities,this._labelRegistry,s,void 0,a,i,t,r?.label_id?(0,p.e)(r.label_id):void 0,`label${E}`);n&&(o=this._filterGroup("label",o,n)),!c&&o.length&&d.push(e("ui.components.target-picker.type.labels")),d.push(...o)}return d})),this._getAdditionalItems=()=>this._getCreateItems(this.createDomains),this._getCreateItems=(0,l.A)((e=>e?.length?e.map((e=>{const t=this.hass.localize("ui.components.entity.entity-picker.create_helper",{domain:(0,M.z)(e)?this.hass.localize(`ui.panel.config.helpers.types.${e}`):(0,$.p$)(this.hass.localize,e)});return{id:Z+e,primary:t,secondary:this.hass.localize("ui.components.entity.entity-picker.new_entity"),icon_path:z}})):[])),this._renderRow=(e,t)=>{if(!e)return c.s6;const i=(0,k.OJ)(e);let s=!1,a=!1,r=!1;return"area"!==i&&"floor"!==i||(e.id=e[i]?.[`${i}_id`],a=(0,m.qC)(this.hass),s="area"===i&&!!e.area?.floor_id),"entity"===i&&(r=!!this._showEntityId),c.qy`
      <ha-combo-box-item
        id=${`list-item-${t}`}
        tabindex="-1"
        .type=${"empty"===i?"text":"button"}
        class=${"empty"===i?"empty":""}
        style=${"area"===e.type&&s?"--md-list-item-leading-space: var(--ha-space-12);":""}
      >
        ${"area"===e.type&&s?c.qy`
              <ha-tree-indicator
                style=${(0,h.W)({width:"var(--ha-space-12)",position:"absolute",top:"var(--ha-space-0)",left:a?void 0:"var(--ha-space-1)",right:a?"var(--ha-space-1)":void 0,transform:a?"scaleX(-1)":""})}
                .end=${e.last}
                slot="start"
              ></ha-tree-indicator>
            `:c.s6}
        ${e.icon?c.qy`<ha-icon slot="start" .icon=${e.icon}></ha-icon>`:e.icon_path?c.qy`<ha-svg-icon
                slot="start"
                .path=${e.icon_path}
              ></ha-svg-icon>`:"entity"===i&&e.stateObj?c.qy`
                  <state-badge
                    slot="start"
                    .stateObj=${e.stateObj}
                    .hass=${this.hass}
                  ></state-badge>
                `:"device"===i&&e.domain?c.qy`
                    <img
                      slot="start"
                      alt=""
                      crossorigin="anonymous"
                      referrerpolicy="no-referrer"
                      src=${(0,D.MR)({domain:e.domain,type:"icon",darkOptimized:this.hass.themes.darkMode})}
                    />
                  `:"floor"===i?c.qy`<ha-floor-icon
                      slot="start"
                      .floor=${e.floor}
                    ></ha-floor-icon>`:"area"===i?c.qy`<ha-svg-icon
                        slot="start"
                        .path=${e.icon_path||V}
                      ></ha-svg-icon>`:c.s6}
        <span slot="headline">${e.primary}</span>
        ${e.secondary?c.qy`<span slot="supporting-text">${e.secondary}</span>`:c.s6}
        ${e.stateObj&&r?c.qy`
              <span slot="supporting-text" class="code">
                ${e.stateObj?.entity_id}
              </span>
            `:c.s6}
        ${!e.domain_name||"entity"===i&&r?c.s6:c.qy`
              <div slot="trailing-supporting-text" class="domain">
                ${e.domain_name}
              </div>
            `}
      </ha-combo-box-item>
    `},this._noTargetFoundLabel=e=>this.hass.localize("ui.components.target-picker.no_target_found",{term:c.qy`<b>‘${e}’</b>`})}}(0,s.__decorate)([(0,d.MZ)({attribute:!1})],O.prototype,"hass",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],O.prototype,"value",void 0),(0,s.__decorate)([(0,d.MZ)()],O.prototype,"helper",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean,reflect:!0})],O.prototype,"compact",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1,type:Array})],O.prototype,"createDomains",void 0),(0,s.__decorate)([(0,d.MZ)({type:Array,attribute:"include-domains"})],O.prototype,"includeDomains",void 0),(0,s.__decorate)([(0,d.MZ)({type:Array,attribute:"include-device-classes"})],O.prototype,"includeDeviceClasses",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],O.prototype,"deviceFilter",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],O.prototype,"entityFilter",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean,reflect:!0})],O.prototype,"disabled",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:"add-on-top",type:Boolean})],O.prototype,"addOnTop",void 0),(0,s.__decorate)([(0,d.wk)()],O.prototype,"_selectedSection",void 0),(0,s.__decorate)([(0,d.wk)()],O.prototype,"_configEntryLookup",void 0),(0,s.__decorate)([(0,d.wk)(),(0,r.Fg)({context:g.HD,subscribe:!0})],O.prototype,"_labelRegistry",void 0),O=(0,s.__decorate)([(0,d.EM)("ha-target-picker")],O),t()}catch(z){t(z)}}))},88422:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),a=i(52630),r=i(96196),n=i(77845),o=e([a]);a=(o.then?(await o)():o)[0];class c extends a.A{static get styles(){return[a.A.styles,r.AH`
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
      `]}constructor(...e){super(...e),this.showDelay=150,this.hideDelay=150}}(0,s.__decorate)([(0,n.MZ)({attribute:"show-delay",type:Number})],c.prototype,"showDelay",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:"hide-delay",type:Number})],c.prototype,"hideDelay",void 0),c=(0,s.__decorate)([(0,n.EM)("ha-tooltip")],c),t()}catch(c){t(c)}}))},41150:function(e,t,i){i.d(t,{D:()=>r});var s=i(92542);const a=()=>i.e("7911").then(i.bind(i,89194)),r=(e,t)=>(0,s.r)(e,"show-dialog",{dialogTag:"ha-dialog-target-details",dialogImport:a,dialogParams:t})},31532:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),a=i(96196),r=i(77845),n=(i(34811),i(42921),i(54167)),o=e([n]);n=(o.then?(await o)():o)[0];class c extends a.WF{render(){let e=0;return Object.values(this.items).forEach((t=>{t&&(e+=t.length)})),a.qy`<ha-expansion-panel
      .expanded=${!this.collapsed}
      left-chevron
      @expanded-changed=${this._expandedChanged}
    >
      <div slot="header" class="heading">
        ${this.hass.localize(`ui.components.target-picker.selected.${this.type}`,{count:e})}
      </div>
      ${Object.entries(this.items).map((([e,t])=>t?t.map((t=>a.qy`<ha-target-picker-item-row
                  .hass=${this.hass}
                  .type=${e}
                  .itemId=${t}
                  .deviceFilter=${this.deviceFilter}
                  .entityFilter=${this.entityFilter}
                  .includeDomains=${this.includeDomains}
                  .includeDeviceClasses=${this.includeDeviceClasses}
                ></ha-target-picker-item-row>`)):a.s6))}
    </ha-expansion-panel>`}_expandedChanged(e){this.collapsed=!e.detail.expanded}constructor(...e){super(...e),this.collapsed=!1}}c.styles=a.AH`
    :host {
      display: block;
      --expansion-panel-content-padding: var(--ha-space-0);
    }
    ha-expansion-panel::part(summary) {
      background-color: var(--ha-color-fill-neutral-quiet-resting);
      padding: var(--ha-space-1) var(--ha-space-2);
      font-weight: var(--ha-font-weight-bold);
      color: var(--secondary-text-color);
      display: flex;
      justify-content: space-between;
      min-height: unset;
    }
    ha-md-list {
      padding: var(--ha-space-0);
    }
  `,(0,s.__decorate)([(0,r.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,s.__decorate)([(0,r.MZ)()],c.prototype,"type",void 0),(0,s.__decorate)([(0,r.MZ)({attribute:!1})],c.prototype,"items",void 0),(0,s.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0})],c.prototype,"collapsed",void 0),(0,s.__decorate)([(0,r.MZ)({attribute:!1})],c.prototype,"deviceFilter",void 0),(0,s.__decorate)([(0,r.MZ)({attribute:!1})],c.prototype,"entityFilter",void 0),(0,s.__decorate)([(0,r.MZ)({type:Array,attribute:"include-domains"})],c.prototype,"includeDomains",void 0),(0,s.__decorate)([(0,r.MZ)({type:Array,attribute:"include-device-classes"})],c.prototype,"includeDeviceClasses",void 0),c=(0,s.__decorate)([(0,r.EM)("ha-target-picker-item-group")],c),t()}catch(c){t(c)}}))},54167:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),a=i(16527),r=i(96196),n=i(77845),o=i(22786),c=i(92542),d=i(56403),h=i(16727),l=i(41144),p=i(87328),u=i(87400),_=i(79599),m=i(3950),y=i(34972),v=i(84125),g=i(6098),b=i(39396),f=i(76681),$=i(26537),x=(i(60733),i(42921),i(23897),i(4148)),k=(i(60961),i(41150)),w=e([x]);x=(w.then?(await w)():w)[0];const M="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",I="M3 6H21V4H3C1.9 4 1 4.9 1 6V18C1 19.1 1.9 20 3 20H7V18H3V6M13 12H9V13.78C8.39 14.33 8 15.11 8 16C8 16.89 8.39 17.67 9 18.22V20H13V18.22C13.61 17.67 14 16.88 14 16S13.61 14.33 13 13.78V12M11 17.5C10.17 17.5 9.5 16.83 9.5 16S10.17 14.5 11 14.5 12.5 15.17 12.5 16 11.83 17.5 11 17.5M22 8H16C15.5 8 15 8.5 15 9V19C15 19.5 15.5 20 16 20H22C22.5 20 23 19.5 23 19V9C23 8.5 22.5 8 22 8M21 18H17V10H21V18Z",C="M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z",D="M17.63,5.84C17.27,5.33 16.67,5 16,5H5A2,2 0 0,0 3,7V17A2,2 0 0,0 5,19H16C16.67,19 17.27,18.66 17.63,18.15L22,12L17.63,5.84Z",L="M20 2H4C2.9 2 2 2.9 2 4V20C2 21.11 2.9 22 4 22H20C21.11 22 22 21.11 22 20V4C22 2.9 21.11 2 20 2M4 6L6 4H10.9L4 10.9V6M4 13.7L13.7 4H18.6L4 18.6V13.7M20 18L18 20H13.1L20 13.1V18M20 10.3L10.3 20H5.4L20 5.4V10.3Z";class q extends r.WF{willUpdate(e){!this.subEntry&&e.has("itemId")&&this._updateItemData()}render(){const{name:e,context:t,iconPath:i,fallbackIconPath:s,stateObject:a,notFound:n}=this._itemData(this.type,this.itemId),o="entity"!==this.type&&!n,c=this.parentEntries||this._entries;return!this.subEntry||"entity"===this.type||c&&0!==c.referenced_entities.length?r.qy`
      <ha-md-list-item type="text" class=${n?"error":""}>
        <div class="icon" slot="start">
          ${this.subEntry?r.qy`
                <div class="horizontal-line-wrapper">
                  <div class="horizontal-line"></div>
                </div>
              `:r.s6}
          ${i?r.qy`<ha-icon .icon=${i}></ha-icon>`:this._iconImg?r.qy`<img
                  alt=${this._domainName||""}
                  crossorigin="anonymous"
                  referrerpolicy="no-referrer"
                  src=${this._iconImg}
                />`:s?r.qy`<ha-svg-icon .path=${s}></ha-svg-icon>`:"entity"===this.type?r.qy`
                      <ha-state-icon
                        .hass=${this.hass}
                        .stateObj=${a||{entity_id:this.itemId,attributes:{}}}
                      >
                      </ha-state-icon>
                    `:r.s6}
        </div>

        <div slot="headline">${e}</div>
        ${n||t&&!this.hideContext?r.qy`<span slot="supporting-text"
              >${n?this.hass.localize(`ui.components.target-picker.${this.type}_not_found`):t}</span
            >`:r.s6}
        ${this._domainName&&this.subEntry?r.qy`<span slot="supporting-text" class="domain"
              >${this._domainName}</span
            >`:r.s6}
        ${!this.subEntry&&c&&o?r.qy`
              <div slot="end" class="summary">
                ${o&&!this.expand&&c?.referenced_entities.length?r.qy`<button class="main link" @click=${this._openDetails}>
                      ${this.hass.localize("ui.components.target-picker.entities_count",{count:c?.referenced_entities.length})}
                    </button>`:o?r.qy`<span class="main">
                        ${this.hass.localize("ui.components.target-picker.entities_count",{count:c?.referenced_entities.length})}
                      </span>`:r.s6}
              </div>
            `:r.s6}
        ${this.expand||this.subEntry?r.s6:r.qy`
              <ha-icon-button
                .path=${M}
                slot="end"
                @click=${this._removeItem}
              ></ha-icon-button>
            `}
      </ha-md-list-item>
      ${this.expand&&c&&c.referenced_entities?this._renderEntries():r.s6}
    `:r.s6}_renderEntries(){const e=this.parentEntries||this._entries;let t="floor"===this.type?"area":"area"===this.type?"device":"entity";"label"===this.type&&(e?.referenced_areas.length?t="area":e?.referenced_devices.length&&(t="device"));const i=("area"===t?e?.referenced_areas:"device"===t&&"label"!==this.type?e?.referenced_devices:"label"!==this.type?e?.referenced_entities:[])||[],s=[],a="entity"===t?void 0:i.map((i=>{const a={referenced_areas:[],referenced_devices:[],referenced_entities:[]};return"area"===t?(a.referenced_devices=e?.referenced_devices.filter((t=>this.hass.devices?.[t]?.area_id===i&&e?.referenced_entities.some((e=>this.hass.entities?.[e]?.device_id===t))))||[],s.push(...a.referenced_devices),a.referenced_entities=e?.referenced_entities.filter((e=>{const t=this.hass.entities[e];return t.area_id===i||!t.device_id||a.referenced_devices.includes(t.device_id)}))||[],a):(a.referenced_entities=e?.referenced_entities.filter((e=>this.hass.entities?.[e]?.device_id===i))||[],a)})),n="label"===this.type&&e?e.referenced_entities.filter((t=>{const i=this.hass.entities[t];return i.labels.includes(this.itemId)&&!e.referenced_devices.includes(i.device_id||"")})):"device"===t&&e?e.referenced_entities.filter((e=>this.hass.entities[e].area_id===this.itemId)):[],o="label"===this.type&&e?e.referenced_devices.filter((e=>!s.includes(e)&&this.hass.devices[e].labels.includes(this.itemId))):[],c=0===o.length?void 0:o.map((t=>({referenced_areas:[],referenced_devices:[],referenced_entities:e?.referenced_entities.filter((e=>this.hass.entities?.[e]?.device_id===t))||[]})));return r.qy`
      <div class="entries-tree">
        <div class="line-wrapper">
          <div class="line"></div>
        </div>
        <ha-md-list class="entries">
          ${i.map(((e,i)=>r.qy`
              <ha-target-picker-item-row
                sub-entry
                .hass=${this.hass}
                .type=${t}
                .itemId=${e}
                .parentEntries=${a?.[i]}
                .hideContext=${this.hideContext||"label"!==this.type}
                expand
              ></ha-target-picker-item-row>
            `))}
          ${o.map(((e,t)=>r.qy`
              <ha-target-picker-item-row
                sub-entry
                .hass=${this.hass}
                type="device"
                .itemId=${e}
                .parentEntries=${c?.[t]}
                .hideContext=${this.hideContext||"label"!==this.type}
                expand
              ></ha-target-picker-item-row>
            `))}
          ${n.map((e=>r.qy`
              <ha-target-picker-item-row
                sub-entry
                .hass=${this.hass}
                type="entity"
                .itemId=${e}
                .hideContext=${this.hideContext||"label"!==this.type}
              ></ha-target-picker-item-row>
            `))}
        </ha-md-list>
      </div>
    `}async _updateItemData(){if("entity"!==this.type)try{const e=await(0,g.F7)(this.hass,{[`${this.type}_id`]:[this.itemId]}),t=[];"floor"!==this.type&&"label"!==this.type||(e.referenced_areas=e.referenced_areas.filter((e=>{const i=this.hass.areas[e];return!("floor"!==this.type&&!i.labels.includes(this.itemId)||!(0,g.Kx)(i,this.hass.devices,this.hass.entities,this.deviceFilter,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter))||(t.push(e),!1)})));const i=[];"floor"!==this.type&&"area"!==this.type&&"label"!==this.type||(e.referenced_devices=e.referenced_devices.filter((e=>{const s=this.hass.devices[e];return!(t.includes(s.area_id||"")||!(0,g.Ly)(s,this.hass.entities,this.deviceFilter,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter))||(i.push(e),!1)}))),e.referenced_entities=e.referenced_entities.filter((t=>{const s=this.hass.entities[t];return!i.includes(s.device_id||"")&&(!!("area"===this.type&&s.area_id===this.itemId||"floor"===this.type&&s.area_id&&e.referenced_areas.includes(s.area_id)||"label"===this.type&&s.labels.includes(this.itemId)||e.referenced_devices.includes(s.device_id||""))&&(0,g.YK)(s,"label"===this.type,this.includeDomains,this.includeDeviceClasses,this.hass.states,this.entityFilter))})),this._entries=e}catch(e){console.error("Failed to extract target",e)}else this._entries=void 0}_setDomainName(e){this._domainName=(0,v.p$)(this.hass.localize,e)}_removeItem(e){e.stopPropagation(),(0,c.r)(this,"remove-target-item",{type:this.type,id:this.itemId})}async _getDeviceDomain(e){try{const t=(await(0,m.Vx)(this.hass,e)).config_entry.domain;this._iconImg=(0,f.MR)({domain:t,type:"icon",darkOptimized:this.hass.themes?.darkMode}),this._setDomainName(t)}catch{}}_openDetails(){(0,k.D)(this,{title:this._itemData(this.type,this.itemId).name,type:this.type,itemId:this.itemId,deviceFilter:this.deviceFilter,entityFilter:this.entityFilter,includeDomains:this.includeDomains,includeDeviceClasses:this.includeDeviceClasses})}constructor(...e){super(...e),this.expand=!1,this.subEntry=!1,this.hideContext=!1,this._itemData=(0,o.A)(((e,t)=>{if("floor"===e){const e=this.hass.floors?.[t];return{name:e?.name||t,iconPath:e?.icon,fallbackIconPath:e?(0,$.Si)(e):C,notFound:!e}}if("area"===e){const e=this.hass.areas?.[t];return{name:e?.name||t,context:e?.floor_id&&this.hass.floors?.[e.floor_id]?.name,iconPath:e?.icon,fallbackIconPath:L,notFound:!e}}if("device"===e){const e=this.hass.devices?.[t];return e?.primary_config_entry&&this._getDeviceDomain(e.primary_config_entry),{name:e?(0,h.T)(e,this.hass):t,context:e?.area_id&&this.hass.areas?.[e.area_id]?.name,fallbackIconPath:I,notFound:!e}}if("entity"===e){this._setDomainName((0,l.m)(t));const e=this.hass.states[t],i=e?(0,p.aH)(e,this.hass.entities,this.hass.devices):t,{area:s,device:a}=e?(0,u.l)(e,this.hass.entities,this.hass.devices,this.hass.areas,this.hass.floors):{area:void 0,device:void 0},r=a?(0,h.xn)(a):void 0,n=[s?(0,d.A)(s):void 0,i?r:void 0].filter(Boolean).join((0,_.qC)(this.hass)?" ◂ ":" ▸ ");return{name:i||r||t,context:n,stateObject:e,notFound:!e&&"all"!==t&&"none"!==t}}const i=this._labelRegistry.find((e=>e.label_id===t));return{name:i?.name||t,iconPath:i?.icon,fallbackIconPath:D,notFound:!i}}))}}q.styles=[b.og,r.AH`
      :host {
        --md-list-item-top-space: var(--ha-space-0);
        --md-list-item-bottom-space: var(--ha-space-0);
        --md-list-item-leading-space: var(--ha-space-2);
        --md-list-item-trailing-space: var(--ha-space-2);
        --md-list-item-two-line-container-height: 56px;
      }

      :host([expand]:not([sub-entry])) ha-md-list-item {
        border: 2px solid var(--ha-color-border-neutral-loud);
        background-color: var(--ha-color-fill-neutral-quiet-resting);
        border-radius: var(--ha-card-border-radius, var(--ha-border-radius-lg));
      }

      .error {
        background: var(--ha-color-fill-warning-quiet-resting);
      }

      .error [slot="supporting-text"] {
        color: var(--ha-color-on-warning-normal);
      }

      state-badge {
        color: var(--ha-color-on-neutral-quiet);
      }

      .icon {
        width: 24px;
        display: flex;
      }

      img {
        width: 24px;
        height: 24px;
        z-index: 1;
      }
      ha-icon-button {
        --mdc-icon-button-size: 32px;
      }
      .summary {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        line-height: var(--ha-line-height-condensed);
      }
      :host([sub-entry]) .summary {
        margin-right: var(--ha-space-12);
      }
      .summary .main {
        font-weight: var(--ha-font-weight-medium);
      }
      .summary .secondary {
        font-size: var(--ha-font-size-s);
        color: var(--secondary-text-color);
      }

      .entries-tree {
        display: flex;
        position: relative;
      }

      .entries-tree .line-wrapper {
        padding: var(--ha-space-5);
      }

      .entries-tree .line-wrapper .line {
        border-left: 2px dashed var(--divider-color);
        height: calc(100% - 28px);
        position: absolute;
        top: 0;
      }

      :host([sub-entry]) .entries-tree .line-wrapper .line {
        height: calc(100% - 12px);
        top: -18px;
      }

      .entries {
        padding: 0;
        --md-item-overflow: visible;
      }

      .horizontal-line-wrapper {
        position: relative;
      }
      .horizontal-line-wrapper .horizontal-line {
        position: absolute;
        top: 11px;
        margin-inline-start: -28px;
        width: 29px;
        border-top: 2px dashed var(--divider-color);
      }

      button.link {
        text-decoration: none;
        color: var(--primary-color);
      }

      button.link:hover,
      button.link:focus {
        text-decoration: underline;
      }

      .domain {
        width: fit-content;
        border-radius: var(--ha-border-radius-md);
        background-color: var(--ha-color-fill-neutral-quiet-resting);
        padding: var(--ha-space-1);
        font-family: var(--ha-font-family-code);
      }
    `],(0,s.__decorate)([(0,n.MZ)({attribute:!1})],q.prototype,"hass",void 0),(0,s.__decorate)([(0,n.MZ)({reflect:!0})],q.prototype,"type",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:"item-id"})],q.prototype,"itemId",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],q.prototype,"expand",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean,attribute:"sub-entry",reflect:!0})],q.prototype,"subEntry",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean,attribute:"hide-context"})],q.prototype,"hideContext",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],q.prototype,"parentEntries",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],q.prototype,"deviceFilter",void 0),(0,s.__decorate)([(0,n.MZ)({attribute:!1})],q.prototype,"entityFilter",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array,attribute:"include-domains"})],q.prototype,"includeDomains",void 0),(0,s.__decorate)([(0,n.MZ)({type:Array,attribute:"include-device-classes"})],q.prototype,"includeDeviceClasses",void 0),(0,s.__decorate)([(0,n.wk)()],q.prototype,"_iconImg",void 0),(0,s.__decorate)([(0,n.wk)()],q.prototype,"_domainName",void 0),(0,s.__decorate)([(0,n.wk)()],q.prototype,"_entries",void 0),(0,s.__decorate)([(0,n.wk)(),(0,a.Fg)({context:y.HD,subscribe:!0})],q.prototype,"_labelRegistry",void 0),(0,s.__decorate)([(0,n.P)("ha-md-list-item")],q.prototype,"item",void 0),(0,s.__decorate)([(0,n.P)("ha-md-list")],q.prototype,"list",void 0),(0,s.__decorate)([(0,n.P)("ha-target-picker-item-row")],q.prototype,"itemRow",void 0),q=(0,s.__decorate)([(0,n.EM)("ha-target-picker-item-row")],q),t()}catch(M){t(M)}}))},60019:function(e,t,i){i.a(e,(async function(e,t){try{var s=i(62826),a=i(16527),r=i(94454),n=i(96196),o=i(77845),c=i(94333),d=i(22786),h=i(10393),l=i(99012),p=i(92542),u=i(16727),_=i(41144),m=i(91889),y=i(93777),v=i(3950),g=i(34972),b=i(84125),f=i(76681),$=i(26537),x=(i(22598),i(60733),i(42921),i(23897),i(4148)),k=i(88422),w=e([x,k]);[x,k]=w.then?(await w)():w;const M="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",I="M3 6H21V4H3C1.9 4 1 4.9 1 6V18C1 19.1 1.9 20 3 20H7V18H3V6M13 12H9V13.78C8.39 14.33 8 15.11 8 16C8 16.89 8.39 17.67 9 18.22V20H13V18.22C13.61 17.67 14 16.88 14 16S13.61 14.33 13 13.78V12M11 17.5C10.17 17.5 9.5 16.83 9.5 16S10.17 14.5 11 14.5 12.5 15.17 12.5 16 11.83 17.5 11 17.5M22 8H16C15.5 8 15 8.5 15 9V19C15 19.5 15.5 20 16 20H22C22.5 20 23 19.5 23 19V9C23 8.5 22.5 8 22 8M21 18H17V10H21V18Z",C="M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z",D="M17.63,5.84C17.27,5.33 16.67,5 16,5H5A2,2 0 0,0 3,7V17A2,2 0 0,0 5,19H16C16.67,19 17.27,18.66 17.63,18.15L22,12L17.63,5.84Z",L="M20 2H4C2.9 2 2 2.9 2 4V20C2 21.11 2.9 22 4 22H20C21.11 22 22 21.11 22 20V4C22 2.9 21.11 2 20 2M4 6L6 4H10.9L4 10.9V6M4 13.7L13.7 4H18.6L4 18.6V13.7M20 18L18 20H13.1L20 13.1V18M20 10.3L10.3 20H5.4L20 5.4V10.3Z",q="M18.17,12L15,8.83L16.41,7.41L21,12L16.41,16.58L15,15.17L18.17,12M5.83,12L9,15.17L7.59,16.59L3,12L7.59,7.42L9,8.83L5.83,12Z";class F extends n.WF{render(){const{name:e,iconPath:t,fallbackIconPath:i,stateObject:s,color:a}=this._itemData(this.type,this.itemId);return n.qy`
      <div
        class="mdc-chip ${(0,c.H)({[this.type]:!0})}"
        style=${a?`--color: rgb(${a}); --background-color: rgba(${a}, .5)`:""}
      >
        ${t?n.qy`<ha-icon
              class="mdc-chip__icon mdc-chip__icon--leading"
              .icon=${t}
            ></ha-icon>`:this._iconImg?n.qy`<img
                class="mdc-chip__icon mdc-chip__icon--leading"
                alt=${this._domainName||""}
                crossorigin="anonymous"
                referrerpolicy="no-referrer"
                src=${this._iconImg}
              />`:i?n.qy`<ha-svg-icon
                  class="mdc-chip__icon mdc-chip__icon--leading"
                  .path=${i}
                ></ha-svg-icon>`:s?n.qy`<ha-state-icon
                    class="mdc-chip__icon mdc-chip__icon--leading"
                    .hass=${this.hass}
                    .stateObj=${s}
                  ></ha-state-icon>`:n.s6}
        <span role="gridcell">
          <span role="button" tabindex="0" class="mdc-chip__primary-action">
            <span id="title-${this.itemId}" class="mdc-chip__text"
              >${e}</span
            >
          </span>
        </span>
        ${"entity"===this.type?n.s6:n.qy`<span role="gridcell">
              <ha-tooltip .for="expand-${(0,y.Y)(this.itemId)}"
                >${this.hass.localize(`ui.components.target-picker.expand_${this.type}_id`)}
              </ha-tooltip>
              <ha-icon-button
                class="expand-btn mdc-chip__icon mdc-chip__icon--trailing"
                .label=${this.hass.localize("ui.components.target-picker.expand")}
                .path=${q}
                hide-title
                .id="expand-${(0,y.Y)(this.itemId)}"
                .type=${this.type}
                @click=${this._handleExpand}
              ></ha-icon-button>
            </span>`}
        <span role="gridcell">
          <ha-tooltip .for="remove-${(0,y.Y)(this.itemId)}">
            ${this.hass.localize(`ui.components.target-picker.remove_${this.type}_id`)}
          </ha-tooltip>
          <ha-icon-button
            class="mdc-chip__icon mdc-chip__icon--trailing"
            .label=${this.hass.localize("ui.components.target-picker.remove")}
            .path=${M}
            hide-title
            .id="remove-${(0,y.Y)(this.itemId)}"
            .type=${this.type}
            @click=${this._removeItem}
          ></ha-icon-button>
        </span>
      </div>
    `}_setDomainName(e){this._domainName=(0,b.p$)(this.hass.localize,e)}async _getDeviceDomain(e){try{const t=(await(0,v.Vx)(this.hass,e)).config_entry.domain;this._iconImg=(0,f.MR)({domain:t,type:"icon",darkOptimized:this.hass.themes?.darkMode}),this._setDomainName(t)}catch{}}_removeItem(e){e.stopPropagation(),(0,p.r)(this,"remove-target-item",{type:this.type,id:this.itemId})}_handleExpand(e){e.stopPropagation(),(0,p.r)(this,"expand-target-item",{type:this.type,id:this.itemId})}constructor(...e){super(...e),this._itemData=(0,d.A)(((e,t)=>{if("floor"===e){const e=this.hass.floors?.[t];return{name:e?.name||t,iconPath:e?.icon,fallbackIconPath:e?(0,$.Si)(e):C}}if("area"===e){const e=this.hass.areas?.[t];return{name:e?.name||t,iconPath:e?.icon,fallbackIconPath:L}}if("device"===e){const e=this.hass.devices?.[t];return e.primary_config_entry&&this._getDeviceDomain(e.primary_config_entry),{name:e?(0,u.T)(e,this.hass):t,fallbackIconPath:I}}if("entity"===e){this._setDomainName((0,_.m)(t));const e=this.hass.states[t];return{name:(0,m.u)(e)||t,stateObject:e}}const i=this._labelRegistry.find((e=>e.label_id===t));let s=i?.color?(0,h.M)(i.color):void 0;if(s?.startsWith("var(")){s=getComputedStyle(this).getPropertyValue(s.substring(4,s.length-1))}return s?.startsWith("#")&&(s=(0,l.xp)(s).join(",")),{name:i?.name||t,iconPath:i?.icon,fallbackIconPath:D,color:s}}))}}F.styles=n.AH`
    ${(0,n.iz)(r)}
    .mdc-chip {
      color: var(--primary-text-color);
    }
    .mdc-chip.add {
      color: rgba(0, 0, 0, 0.87);
    }
    .add-container {
      position: relative;
      display: inline-flex;
    }
    .mdc-chip:not(.add) {
      cursor: default;
    }
    .mdc-chip ha-icon-button {
      --mdc-icon-button-size: 24px;
      display: flex;
      align-items: center;
      outline: none;
    }
    .mdc-chip ha-icon-button ha-svg-icon {
      border-radius: 50%;
      background: var(--secondary-text-color);
    }
    .mdc-chip__icon.mdc-chip__icon--trailing {
      width: var(--ha-space-4);
      height: var(--ha-space-4);
      --mdc-icon-size: 14px;
      color: var(--secondary-text-color);
      margin-inline-start: var(--ha-space-1) !important;
      margin-inline-end: calc(-1 * var(--ha-space-1)) !important;
      direction: var(--direction);
    }
    .mdc-chip__icon--leading {
      display: flex;
      align-items: center;
      justify-content: center;
      --mdc-icon-size: 20px;
      border-radius: var(--ha-border-radius-circle);
      padding: 6px;
      margin-left: -13px !important;
      margin-inline-start: -13px !important;
      margin-inline-end: var(--ha-space-1) !important;
      direction: var(--direction);
    }
    .expand-btn {
      margin-right: var(--ha-space-0);
      margin-inline-end: var(--ha-space-0);
      margin-inline-start: initial;
    }
    .mdc-chip.area:not(.add),
    .mdc-chip.floor:not(.add) {
      border: 1px solid #fed6a4;
      background: var(--card-background-color);
    }
    .mdc-chip.area:not(.add) .mdc-chip__icon--leading,
    .mdc-chip.area.add,
    .mdc-chip.floor:not(.add) .mdc-chip__icon--leading,
    .mdc-chip.floor.add {
      background: #fed6a4;
    }
    .mdc-chip.device:not(.add) {
      border: 1px solid #a8e1fb;
      background: var(--card-background-color);
    }
    .mdc-chip.device:not(.add) .mdc-chip__icon--leading,
    .mdc-chip.device.add {
      background: #a8e1fb;
    }
    .mdc-chip.entity:not(.add) {
      border: 1px solid #d2e7b9;
      background: var(--card-background-color);
    }
    .mdc-chip.entity:not(.add) .mdc-chip__icon--leading,
    .mdc-chip.entity.add {
      background: #d2e7b9;
    }
    .mdc-chip.label:not(.add) {
      border: 1px solid var(--color, #e0e0e0);
      background: var(--card-background-color);
    }
    .mdc-chip.label:not(.add) .mdc-chip__icon--leading,
    .mdc-chip.label.add {
      background: var(--background-color, #e0e0e0);
    }
    .mdc-chip:hover {
      z-index: 5;
    }
    :host([disabled]) .mdc-chip {
      opacity: var(--light-disabled-opacity);
      pointer-events: none;
    }
    .tooltip-icon-img {
      width: 24px;
      height: 24px;
    }
  `,(0,s.__decorate)([(0,o.MZ)({attribute:!1})],F.prototype,"hass",void 0),(0,s.__decorate)([(0,o.MZ)()],F.prototype,"type",void 0),(0,s.__decorate)([(0,o.MZ)({attribute:"item-id"})],F.prototype,"itemId",void 0),(0,s.__decorate)([(0,o.wk)()],F.prototype,"_domainName",void 0),(0,s.__decorate)([(0,o.wk)()],F.prototype,"_iconImg",void 0),(0,s.__decorate)([(0,o.wk)(),(0,a.Fg)({context:g.HD,subscribe:!0})],F.prototype,"_labelRegistry",void 0),F=(0,s.__decorate)([(0,o.EM)("ha-target-picker-value-chip")],F),t()}catch(M){t(M)}}))},34972:function(e,t,i){i.d(t,{$F:()=>c,HD:()=>l,X1:()=>r,iN:()=>a,ih:()=>d,rf:()=>h,wn:()=>o,xJ:()=>n});var s=i(16527);(0,s.q6)("connection");const a=(0,s.q6)("states"),r=(0,s.q6)("entities"),n=(0,s.q6)("devices"),o=(0,s.q6)("areas"),c=(0,s.q6)("localize"),d=((0,s.q6)("locale"),(0,s.q6)("config"),(0,s.q6)("themes"),(0,s.q6)("selectedTheme"),(0,s.q6)("user"),(0,s.q6)("userData"),(0,s.q6)("panels"),(0,s.q6)("extendedEntities")),h=(0,s.q6)("floors"),l=(0,s.q6)("labels")},22800:function(e,t,i){i.d(t,{BM:()=>f,Bz:()=>v,G3:()=>u,G_:()=>_,Ox:()=>g,P9:()=>b,jh:()=>l,v:()=>p,wz:()=>$});var s=i(70570),a=i(22786),r=i(41144),n=i(79384),o=i(91889),c=(i(25749),i(79599)),d=i(40404),h=i(84125);const l=(e,t)=>{if(t.name)return t.name;const i=e.states[t.entity_id];return i?(0,o.u)(i):t.original_name?t.original_name:t.entity_id},p=(e,t)=>e.callWS({type:"config/entity_registry/get",entity_id:t}),u=(e,t)=>e.callWS({type:"config/entity_registry/get_entries",entity_ids:t}),_=(e,t,i)=>e.callWS({type:"config/entity_registry/update",entity_id:t,...i}),m=e=>e.sendMessagePromise({type:"config/entity_registry/list"}),y=(e,t)=>e.subscribeEvents((0,d.s)((()=>m(e).then((e=>t.setState(e,!0)))),500,!0),"entity_registry_updated"),v=(e,t)=>(0,s.N)("_entityRegistry",m,y,e,t),g=(0,a.A)((e=>{const t={};for(const i of e)t[i.entity_id]=i;return t})),b=(0,a.A)((e=>{const t={};for(const i of e)t[i.id]=i;return t})),f=(e,t)=>e.callWS({type:"config/entity_registry/get_automatic_entity_ids",entity_ids:t}),$=(e,t,i,s,a,d,l,p,u,_="")=>{let m=[],y=Object.keys(e.states);return l&&(y=y.filter((e=>l.includes(e)))),p&&(y=y.filter((e=>!p.includes(e)))),t&&(y=y.filter((e=>t.includes((0,r.m)(e))))),i&&(y=y.filter((e=>!i.includes((0,r.m)(e))))),m=y.map((t=>{const i=e.states[t],s=(0,o.u)(i),[a,d,l]=(0,n.Cf)(i,[{type:"entity"},{type:"device"},{type:"area"}],e.entities,e.devices,e.areas,e.floors),p=(0,h.p$)(e.localize,(0,r.m)(t)),u=(0,c.qC)(e),m=a||d||t,y=[l,a?d:void 0].filter(Boolean).join(u?" ◂ ":" ▸ ");return{id:`${_}${t}`,primary:m,secondary:y,domain_name:p,sorting_label:[d,a].filter(Boolean).join("_"),search_labels:[a,d,l,p,s,t].filter(Boolean),stateObj:i}})),a&&(m=m.filter((e=>e.id===u||e.stateObj?.attributes.device_class&&a.includes(e.stateObj.attributes.device_class)))),d&&(m=m.filter((e=>e.id===u||e.stateObj?.attributes.unit_of_measurement&&d.includes(e.stateObj.attributes.unit_of_measurement)))),s&&(m=m.filter((e=>e.id===u||e.stateObj&&s(e.stateObj)))),m}},28441:function(e,t,i){i.d(t,{c:()=>r});const s=async(e,t,i,a,r,...n)=>{const o=r,c=o[e],d=c=>a&&a(r,c.result)!==c.cacheKey?(o[e]=void 0,s(e,t,i,a,r,...n)):c.result;if(c)return c instanceof Promise?c.then(d):d(c);const h=i(r,...n);return o[e]=h,h.then((i=>{o[e]={result:i,cacheKey:a?.(r,i)},setTimeout((()=>{o[e]=void 0}),t)}),(()=>{o[e]=void 0})),h},a=e=>e.callWS({type:"entity/source"}),r=e=>s("_entitySources",3e4,a,(e=>Object.keys(e.states).length),e)},10085:function(e,t,i){i.d(t,{E:()=>r});var s=i(62826),a=i(77845);const r=e=>{class t extends e{connectedCallback(){super.connectedCallback(),this._checkSubscribed()}disconnectedCallback(){if(super.disconnectedCallback(),this.__unsubs){for(;this.__unsubs.length;){const e=this.__unsubs.pop();e instanceof Promise?e.then((e=>e())):e()}this.__unsubs=void 0}}updated(e){if(super.updated(e),e.has("hass"))this._checkSubscribed();else if(this.hassSubscribeRequiredHostProps)for(const t of e.keys())if(this.hassSubscribeRequiredHostProps.includes(t))return void this._checkSubscribed()}hassSubscribe(){return[]}_checkSubscribed(){void 0===this.__unsubs&&this.isConnected&&void 0!==this.hass&&!this.hassSubscribeRequiredHostProps?.some((e=>void 0===this[e]))&&(this.__unsubs=this.hassSubscribe())}}return(0,s.__decorate)([(0,a.MZ)({attribute:!1})],t.prototype,"hass",void 0),t}},64070:function(e,t,i){i.d(t,{$:()=>r});var s=i(92542);const a=()=>i.e("8991").then(i.bind(i,40386)),r=(e,t)=>{(0,s.r)(e,"show-dialog",{dialogTag:"dialog-helper-detail",dialogImport:a,dialogParams:t})}},76681:function(e,t,i){i.d(t,{MR:()=>s,a_:()=>a,bg:()=>r});const s=e=>`https://brands.home-assistant.io/${e.brand?"brands/":""}${e.useFallback?"_/":""}${e.domain}/${e.darkOptimized?"dark_":""}${e.type}.png`,a=e=>e.split("/")[4],r=e=>e.startsWith("https://brands.home-assistant.io/")}};
//# sourceMappingURL=3161.9cccb86a25dcf48d.js.map