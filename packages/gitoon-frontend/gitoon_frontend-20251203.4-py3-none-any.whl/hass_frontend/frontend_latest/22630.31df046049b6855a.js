/*! For license information please see 22630.31df046049b6855a.js.LICENSE.txt */
export const __webpack_id__="22630";export const __webpack_ids__=["22630"];export const __webpack_modules__={69093:function(e,t,a){a.d(t,{t:()=>r});var o=a(71727);const r=e=>(0,o.m)(e.entity_id)},82286:function(e,t,a){a.d(t,{$:()=>o});const o=(e,t)=>r(e.attributes,t),r=(e,t)=>0!==(e.supported_features&t)},72554:function(e,t,a){a.d(t,{l:()=>c});var o=a(62826),r=a(30728),n=a(47705),i=a(96196),s=a(44457);a(22444),a(26300);const l=["button","ha-list-item"],c=(e,t)=>i.qy` <div class="header_title"> <ha-icon-button .label="${e?.localize("ui.common.close")??"Close"}" .path="${"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"}" dialogAction="close" class="header_button"></ha-icon-button> <span>${t}</span> </div> `;class d extends r.u{scrollToPos(e,t){this.contentElement?.scrollTo(e,t)}renderHeading(){return i.qy`<slot name="heading"> ${super.renderHeading()} </slot>`}firstUpdated(){super.firstUpdated(),this.suppressDefaultPressSelector=[this.suppressDefaultPressSelector,l].join(", "),this._updateScrolledAttribute(),this.contentElement?.addEventListener("scroll",this._onScroll,{passive:!0})}disconnectedCallback(){super.disconnectedCallback(),this.contentElement.removeEventListener("scroll",this._onScroll)}_updateScrolledAttribute(){this.contentElement&&this.toggleAttribute("scrolled",0!==this.contentElement.scrollTop)}constructor(...e){super(...e),this._onScroll=()=>{this._updateScrolledAttribute()}}}d.styles=[n.R,i.AH`:host([scrolled]) ::slotted(ha-dialog-header){border-bottom:1px solid var(--mdc-dialog-scroll-divider-color,rgba(0,0,0,.12))}.mdc-dialog{--mdc-dialog-scroll-divider-color:var(
          --dialog-scroll-divider-color,
          var(--divider-color)
        );z-index:var(--dialog-z-index,8);-webkit-backdrop-filter:var(--ha-dialog-scrim-backdrop-filter,var(--dialog-backdrop-filter,none));backdrop-filter:var(--ha-dialog-scrim-backdrop-filter,var(--dialog-backdrop-filter,none));--mdc-dialog-box-shadow:var(--dialog-box-shadow, none);--mdc-typography-headline6-font-weight:var(--ha-font-weight-normal);--mdc-typography-headline6-font-size:1.574rem}.mdc-dialog__actions{justify-content:var(--justify-action-buttons,flex-end);padding:var(--ha-space-3) var(--ha-space-4) var(--ha-space-4) var(--ha-space-4)}.mdc-dialog__actions span:first-child{flex:var(--secondary-action-button-flex,unset)}.mdc-dialog__actions span:nth-child(2){flex:var(--primary-action-button-flex,unset)}.mdc-dialog__container{align-items:var(--vertical-align-dialog,center);padding:var(--dialog-container-padding,var(--ha-space-0))}.mdc-dialog__title{padding:var(--ha-space-4) var(--ha-space-4) var(--ha-space-0) var(--ha-space-4)}.mdc-dialog__title:has(span){padding:var(--ha-space-3) var(--ha-space-3) var(--ha-space-0)}.mdc-dialog__title::before{content:unset}.mdc-dialog .mdc-dialog__content{position:var(--dialog-content-position,relative);padding:var(--dialog-content-padding,var(--ha-space-6))}:host([hideactions]) .mdc-dialog .mdc-dialog__content{padding-bottom:var(--dialog-content-padding,var(--ha-space-6))}.mdc-dialog .mdc-dialog__surface{position:var(--dialog-surface-position,relative);top:var(--dialog-surface-top);margin-top:var(--dialog-surface-margin-top);min-width:var(--mdc-dialog-min-width,auto);min-height:var(--mdc-dialog-min-height,auto);border-radius:var(--ha-dialog-border-radius,var(--ha-border-radius-3xl));-webkit-backdrop-filter:var(--ha-dialog-surface-backdrop-filter,none);backdrop-filter:var(--ha-dialog-surface-backdrop-filter,none);background:var(--ha-dialog-surface-background,var(--mdc-theme-surface,#fff));padding:var(--dialog-surface-padding,var(--ha-space-0))}:host([flexContent]) .mdc-dialog .mdc-dialog__content{display:flex;flex-direction:column}.header_title{display:flex;align-items:center;direction:var(--direction)}.header_title span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;padding-left:var(--ha-space-1);padding-right:var(--ha-space-1);margin-right:var(--ha-space-3);margin-inline-end:var(--ha-space-3);margin-inline-start:initial}.header_button{text-decoration:none;color:inherit;inset-inline-start:initial;inset-inline-end:calc(var(--ha-space-3) * -1);direction:var(--direction)}.dialog-actions{inset-inline-start:initial!important;inset-inline-end:var(--ha-space-0)!important;direction:var(--direction)}`],d=(0,o.__decorate)([(0,s.EM)("ha-dialog")],d)},69709:function(e,t,a){a(18111),a(22489),a(61701),a(18237);var o=a(62826),r=a(96196),n=a(44457),i=a(1420),s=a(30015),l=a.n(s),c=a(1087),d=(a(14603),a(47566),a(98721),a(2209));let h;var p=a(996);const u=e=>r.qy`${e}`,m=new p.G(1e3),g={reType:/(?<input>(\[!(?<type>caution|important|note|tip|warning)\])(?:\s|\\n)?)/i,typeToHaAlert:{caution:"error",important:"info",note:"info",tip:"success",warning:"warning"}};class _ extends r.mN{disconnectedCallback(){if(super.disconnectedCallback(),this.cache){const e=this._computeCacheKey();m.set(e,this.innerHTML)}}createRenderRoot(){return this}update(e){super.update(e),void 0!==this.content&&(this._renderPromise=this._render())}async getUpdateComplete(){return await super.getUpdateComplete(),await this._renderPromise,!0}willUpdate(e){if(!this.innerHTML&&this.cache){const e=this._computeCacheKey();m.has(e)&&((0,r.XX)(u((0,i._)(m.get(e))),this.renderRoot),this._resize())}}_computeCacheKey(){return l()({content:this.content,allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl,breaks:this.breaks})}async _render(){const e=await(async(e,t,o)=>(h||(h=(0,d.LV)(new Worker(new URL(a.p+a.u("55640"),a.b)))),h.renderMarkdown(e,t,o)))(String(this.content),{breaks:this.breaks,gfm:!0},{allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl});(0,r.XX)(u((0,i._)(e.join(""))),this.renderRoot),this._resize();const t=document.createTreeWalker(this,NodeFilter.SHOW_ELEMENT,null);for(;t.nextNode();){const e=t.currentNode;if(e instanceof HTMLAnchorElement&&e.host!==document.location.host)e.target="_blank",e.rel="noreferrer noopener";else if(e instanceof HTMLImageElement)this.lazyImages&&(e.loading="lazy"),e.addEventListener("load",this._resize);else if(e instanceof HTMLQuoteElement){const a=e.firstElementChild?.firstChild?.textContent&&g.reType.exec(e.firstElementChild.firstChild.textContent);if(a){const{type:o}=a.groups,r=document.createElement("ha-alert");r.alertType=g.typeToHaAlert[o.toLowerCase()],r.append(...Array.from(e.childNodes).map(e=>{const t=Array.from(e.childNodes);if(!this.breaks&&t.length){const e=t[0];e.nodeType===Node.TEXT_NODE&&e.textContent===a.input&&e.textContent?.includes("\n")&&(e.textContent=e.textContent.split("\n").slice(1).join("\n"))}return t}).reduce((e,t)=>e.concat(t),[]).filter(e=>e.textContent&&e.textContent!==a.input)),t.parentNode().replaceChild(r,e)}}else e instanceof HTMLElement&&["ha-alert","ha-qr-code","ha-icon","ha-svg-icon"].includes(e.localName)&&a(96175)(`./${e.localName}`)}}constructor(...e){super(...e),this.allowSvg=!1,this.allowDataUrl=!1,this.breaks=!1,this.lazyImages=!1,this.cache=!1,this._renderPromise=Promise.resolve(),this._resize=()=>(0,c.r)(this,"content-resize")}}(0,o.__decorate)([(0,n.MZ)()],_.prototype,"content",void 0),(0,o.__decorate)([(0,n.MZ)({attribute:"allow-svg",type:Boolean})],_.prototype,"allowSvg",void 0),(0,o.__decorate)([(0,n.MZ)({attribute:"allow-data-url",type:Boolean})],_.prototype,"allowDataUrl",void 0),(0,o.__decorate)([(0,n.MZ)({type:Boolean})],_.prototype,"breaks",void 0),(0,o.__decorate)([(0,n.MZ)({type:Boolean,attribute:"lazy-images"})],_.prototype,"lazyImages",void 0),(0,o.__decorate)([(0,n.MZ)({type:Boolean})],_.prototype,"cache",void 0),_=(0,o.__decorate)([(0,n.EM)("ha-markdown-element")],_)},3587:function(e,t,a){var o=a(62826),r=a(96196),n=a(44457);a(69709);class i extends r.WF{async getUpdateComplete(){const e=await super.getUpdateComplete();return await(this._markdownElement?.updateComplete),e}render(){return this.content?r.qy`<ha-markdown-element .content="${this.content}" .allowSvg="${this.allowSvg}" .allowDataUrl="${this.allowDataUrl}" .breaks="${this.breaks}" .lazyImages="${this.lazyImages}" .cache="${this.cache}"></ha-markdown-element>`:r.s6}constructor(...e){super(...e),this.allowSvg=!1,this.allowDataUrl=!1,this.breaks=!1,this.lazyImages=!1,this.cache=!1}}i.styles=r.AH`
    :host {
      display: block;
    }
    ha-markdown-element {
      -ms-user-select: text;
      -webkit-user-select: text;
      -moz-user-select: text;
    }
    ha-markdown-element > *:first-child {
      margin-top: 0;
    }
    ha-markdown-element > *:last-child {
      margin-bottom: 0;
    }
    ha-alert {
      display: block;
      margin: var(--ha-space-1) 0;
    }
    a {
      color: var(--markdown-link-color, var(--primary-color));
    }
    img {
      background-color: var(--markdown-image-background-color);
      border-radius: var(--markdown-image-border-radius);
      max-width: 100%;
    }
    p:first-child > img:first-child {
      vertical-align: top;
    }
    p:first-child > img:last-child {
      vertical-align: top;
    }
    ha-markdown-element > :is(ol, ul) {
      padding-inline-start: var(--markdown-list-indent, revert);
    }
    li {
      &:has(input[type="checkbox"]) {
        list-style: none;
        & > input[type="checkbox"] {
          margin-left: 0;
        }
      }
    }
    svg {
      background-color: var(--markdown-svg-background-color, none);
      color: var(--markdown-svg-color, none);
    }
    code,
    pre {
      background-color: var(--markdown-code-background-color, none);
      border-radius: var(--ha-border-radius-sm);
      color: var(--markdown-code-text-color, inherit);
    }
    code {
      font-size: var(--ha-font-size-s);
      padding: 0.2em 0.4em;
    }
    pre code {
      padding: 0;
    }
    pre {
      padding: var(--ha-space-4);
      overflow: auto;
      line-height: var(--ha-line-height-condensed);
      font-family: var(--ha-font-family-code);
    }
    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      line-height: initial;
    }
    h2 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-bold);
    }
    hr {
      border-color: var(--divider-color);
      border-bottom: none;
      margin: var(--ha-space-4) 0;
    }
    table[role="presentation"] {
      --markdown-table-border-collapse: separate;
      --markdown-table-border-width: attr(border, 0);
      --markdown-table-padding-inline: 0;
      --markdown-table-padding-block: 0;
      th {
        vertical-align: attr(align, center);
      }
      td {
        vertical-align: attr(align, left);
      }
    }
    table {
      border-collapse: var(--markdown-table-border-collapse, collapse);
    }
    div:has(> table) {
      overflow: auto;
    }
    th {
      text-align: var(--markdown-table-text-align, start);
    }
    td,
    th {
      border-width: var(--markdown-table-border-width, 1px);
      border-style: var(--markdown-table-border-style, solid);
      border-color: var(--markdown-table-border-color, var(--divider-color));
      padding-inline: var(--markdown-table-padding-inline, 0.5em);
      padding-block: var(--markdown-table-padding-block, 0.25em);
    }
    blockquote {
      border-left: 4px solid var(--divider-color);
      margin-inline: 0;
      padding-inline: 1em;
    }
  `,(0,o.__decorate)([(0,n.MZ)()],i.prototype,"content",void 0),(0,o.__decorate)([(0,n.MZ)({attribute:"allow-svg",type:Boolean})],i.prototype,"allowSvg",void 0),(0,o.__decorate)([(0,n.MZ)({attribute:"allow-data-url",type:Boolean})],i.prototype,"allowDataUrl",void 0),(0,o.__decorate)([(0,n.MZ)({type:Boolean})],i.prototype,"breaks",void 0),(0,o.__decorate)([(0,n.MZ)({type:Boolean,attribute:"lazy-images"})],i.prototype,"lazyImages",void 0),(0,o.__decorate)([(0,n.MZ)({type:Boolean})],i.prototype,"cache",void 0),(0,o.__decorate)([(0,n.P)("ha-markdown-element")],i.prototype,"_markdownElement",void 0),i=(0,o.__decorate)([(0,n.EM)("ha-markdown")],i)},15056:function(e,t,a){a.a(e,async function(e,o){try{a.r(t);var r=a(62826),n=a(96196),i=a(44457),s=a(18350),l=(a(72554),a(52763),a(3587),a(65829)),c=a(82e3),d=a(14503),h=e([s,l]);[s,l]=h.then?(await h)():h;let p=0;class u extends n.WF{showDialog({continueFlowId:e,mfaModuleId:t,dialogClosedCallback:a}){this._instance=p++,this._dialogClosedCallback=a,this._opened=!0;const o=e?this.hass.callWS({type:"auth/setup_mfa",flow_id:e}):this.hass.callWS({type:"auth/setup_mfa",mfa_module_id:t}),r=this._instance;o.then(e=>{r===this._instance&&this._processStep(e)})}closeDialog(){this._step&&this._flowDone(),this._opened=!1}render(){return this._opened?n.qy` <ha-dialog open .heading="${this._computeStepTitle()}" @closed="${this.closeDialog}"> <div> ${this._errorMessage?n.qy`<div class="error">${this._errorMessage}</div>`:""} ${this._step?n.qy`${"abort"===this._step.type?n.qy` <ha-markdown allow-svg breaks .content="${this.hass.localize(`component.auth.mfa_setup.${this._step.handler}.abort.${this._step.reason}`)}"></ha-markdown>`:"create_entry"===this._step.type?n.qy`<p> ${this.hass.localize("ui.panel.profile.mfa_setup.step_done",{step:this._step.title||this._step.handler})} </p>`:"form"===this._step.type?n.qy`<ha-markdown allow-svg breaks .content="${this.hass.localize(`component.auth.mfa_setup.${this._step.handler}.step.${this._step.step_id}.description`,this._step.description_placeholders)}"></ha-markdown> <ha-form .hass="${this.hass}" .data="${this._stepData}" .schema="${(0,c.Hg)(this._step.data_schema)}" .error="${this._step.errors}" .computeLabel="${this._computeLabel}" .computeError="${this._computeError}" @value-changed="${this._stepDataChanged}"></ha-form>`:""}`:n.qy`<div class="init-spinner"> <ha-spinner></ha-spinner> </div>`} </div> <ha-button slot="primaryAction" @click="${this.closeDialog}" appearance="${["abort","create_entry"].includes(this._step?.type||"")?"accent":"plain"}">${this.hass.localize(["abort","create_entry"].includes(this._step?.type||"")?"ui.panel.profile.mfa_setup.close":"ui.common.cancel")}</ha-button> ${"form"===this._step?.type?n.qy`<ha-button slot="primaryAction" .disabled="${this._loading}" @click="${this._submitStep}">${this.hass.localize("ui.panel.profile.mfa_setup.submit")}</ha-button>`:n.s6} </ha-dialog> `:n.s6}static get styles(){return[d.nA,n.AH`.error{color:red}ha-dialog{max-width:500px}ha-markdown{--markdown-svg-background-color:white;--markdown-svg-color:black;display:block;margin:0 auto}ha-markdown a{color:var(--primary-color)}ha-markdown-element p{text-align:center}ha-markdown-element code{background-color:transparent}ha-markdown-element>:last-child{margin-bottom:revert}.init-spinner{padding:10px 100px 34px;text-align:center}`]}firstUpdated(e){super.firstUpdated(e),this.hass.loadBackendTranslation("mfa_setup","auth"),this.addEventListener("keypress",e=>{"Enter"===e.key&&this._submitStep()})}_stepDataChanged(e){this._stepData=e.detail.value}_submitStep(){this._loading=!0,this._errorMessage=void 0;const e=this._instance;this.hass.callWS({type:"auth/setup_mfa",flow_id:this._step.flow_id,user_input:this._stepData}).then(t=>{e===this._instance&&(this._processStep(t),this._loading=!1)},e=>{this._errorMessage=e&&e.body&&e.body.message||"Unknown error occurred",this._loading=!1})}_processStep(e){e.errors||(e.errors={}),this._step=e,0===Object.keys(e.errors).length&&(this._stepData={})}_flowDone(){const e=Boolean(this._step&&["create_entry","abort"].includes(this._step.type));this._dialogClosedCallback({flowFinished:e}),this._errorMessage=void 0,this._step=void 0,this._stepData={},this._dialogClosedCallback=void 0,this.closeDialog()}_computeStepTitle(){return"abort"===this._step?.type?this.hass.localize("ui.panel.profile.mfa_setup.title_aborted"):"create_entry"===this._step?.type?this.hass.localize("ui.panel.profile.mfa_setup.title_success"):"form"===this._step?.type?this.hass.localize(`component.auth.mfa_setup.${this._step.handler}.step.${this._step.step_id}.title`):""}constructor(...e){super(...e),this._loading=!1,this._opened=!1,this._stepData={},this._computeLabel=e=>this.hass.localize(`component.auth.mfa_setup.${this._step.handler}.step.${this._step.step_id}.data.${e.name}`)||e.name,this._computeError=e=>this.hass.localize(`component.auth.mfa_setup.${this._step.handler}.error.${e}`)||e}}(0,r.__decorate)([(0,i.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,r.__decorate)([(0,i.wk)()],u.prototype,"_dialogClosedCallback",void 0),(0,r.__decorate)([(0,i.wk)()],u.prototype,"_instance",void 0),(0,r.__decorate)([(0,i.wk)()],u.prototype,"_loading",void 0),(0,r.__decorate)([(0,i.wk)()],u.prototype,"_opened",void 0),(0,r.__decorate)([(0,i.wk)()],u.prototype,"_stepData",void 0),(0,r.__decorate)([(0,i.wk)()],u.prototype,"_step",void 0),(0,r.__decorate)([(0,i.wk)()],u.prototype,"_errorMessage",void 0),u=(0,r.__decorate)([(0,i.EM)("ha-mfa-module-setup-flow")],u),o()}catch(e){o(e)}})},996:function(e,t,a){a.d(t,{G:()=>o});class o{get(e){return this._cache.get(e)}set(e,t){this._cache.set(e,t),this._expiration&&window.setTimeout(()=>this._cache.delete(e),this._expiration)}has(e){return this._cache.has(e)}constructor(e){this._cache=new Map,this._expiration=e}}},96175:function(e,t,a){var o={"./ha-icon-prev":["89133","61982"],"./ha-icon-button-toolbar":["9882","26431","76775"],"./ha-alert":["38962","19695"],"./ha-icon-button-toggle":["62501","77254"],"./ha-svg-icon.ts":["67094"],"./ha-alert.ts":["38962","19695"],"./ha-icon":["88945","51146"],"./ha-icon-next.ts":["43661","63902"],"./ha-qr-code.ts":["60543","51343","62740"],"./ha-icon-overflow-menu.ts":["75248","46095","26431","22016","56297"],"./ha-icon-button-toggle.ts":["62501","77254"],"./ha-icon-button-group":["39826","13647"],"./ha-svg-icon":["67094"],"./ha-icon-button-prev":["45100","99197"],"./ha-icon-button.ts":["26300"],"./ha-icon-overflow-menu":["75248","46095","26431","22016","56297"],"./ha-icon-button-arrow-next":["99028","54101"],"./ha-icon-button-prev.ts":["45100","99197"],"./ha-icon-picker":["64138","44533","7199","46095","48654","72991"],"./ha-icon-button-toolbar.ts":["9882","26431","76775"],"./ha-icon-button-arrow-prev.ts":["90248","17041"],"./ha-icon-button-next":["25440","81049"],"./ha-icon-next":["43661","63902"],"./ha-icon-picker.ts":["64138","44533","7199","46095","48654","72991"],"./ha-icon-prev.ts":["89133","61982"],"./ha-icon-button-arrow-prev":["90248","17041"],"./ha-icon-button-next.ts":["25440","81049"],"./ha-icon.ts":["88945","51146"],"./ha-qr-code":["60543","51343","62740"],"./ha-icon-button":["26300"],"./ha-icon-button-group.ts":["39826","13647"],"./ha-icon-button-arrow-next.ts":["99028","54101"]};function r(e){if(!a.o(o,e))return Promise.resolve().then(function(){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t});var t=o[e],r=t[0];return Promise.all(t.slice(1).map(a.e)).then(function(){return a(r)})}r.keys=()=>Object.keys(o),r.id=96175,e.exports=r},48646:function(e,t,a){var o=a(69565),r=a(28551),n=a(1767),i=a(50851);e.exports=function(e,t){t&&"string"==typeof e||r(e);var a=i(e);return n(r(void 0!==a?o(a,e):e))}},30531:function(e,t,a){var o=a(46518),r=a(69565),n=a(79306),i=a(28551),s=a(1767),l=a(48646),c=a(19462),d=a(9539),h=a(96395),p=a(30684),u=a(84549),m=!h&&!p("flatMap",function(){}),g=!h&&!m&&u("flatMap",TypeError),_=h||m||g,v=c(function(){for(var e,t,a=this.iterator,o=this.mapper;;){if(t=this.inner)try{if(!(e=i(r(t.next,t.iterator))).done)return e.value;this.inner=null}catch(e){d(a,"throw",e)}if(e=i(r(this.next,a)),this.done=!!e.done)return;try{this.inner=l(o(e.value,this.counter++),!1)}catch(e){d(a,"throw",e)}}});o({target:"Iterator",proto:!0,real:!0,forced:_},{flatMap:function(e){i(this);try{n(e)}catch(e){d(this,"throw",e)}return g?r(g,this,e):new v(s(this),{mapper:e,inner:null})}})},2209:function(e,t,a){a.d(t,{LV:()=>p});a(18111),a(61701),a(18237);const o=Symbol("Comlink.proxy"),r=Symbol("Comlink.endpoint"),n=Symbol("Comlink.releaseProxy"),i=Symbol("Comlink.finalizer"),s=Symbol("Comlink.thrown"),l=e=>"object"==typeof e&&null!==e||"function"==typeof e,c=new Map([["proxy",{canHandle:e=>l(e)&&e[o],serialize(e){const{port1:t,port2:a}=new MessageChannel;return d(e,t),[a,[a]]},deserialize:e=>(e.start(),p(e))}],["throw",{canHandle:e=>l(e)&&s in e,serialize({value:e}){let t;return t=e instanceof Error?{isError:!0,value:{message:e.message,name:e.name,stack:e.stack}}:{isError:!1,value:e},[t,[]]},deserialize(e){if(e.isError)throw Object.assign(new Error(e.value.message),e.value);throw e.value}}]]);function d(e,t=globalThis,a=["*"]){t.addEventListener("message",function r(n){if(!n||!n.data)return;if(!function(e,t){for(const a of e){if(t===a||"*"===a)return!0;if(a instanceof RegExp&&a.test(t))return!0}return!1}(a,n.origin))return void console.warn(`Invalid origin '${n.origin}' for comlink proxy`);const{id:l,type:c,path:p}=Object.assign({path:[]},n.data),u=(n.data.argumentList||[]).map(w);let m;try{const t=p.slice(0,-1).reduce((e,t)=>e[t],e),a=p.reduce((e,t)=>e[t],e);switch(c){case"GET":m=a;break;case"SET":t[p.slice(-1)[0]]=w(n.data.value),m=!0;break;case"APPLY":m=a.apply(t,u);break;case"CONSTRUCT":m=function(e){return Object.assign(e,{[o]:!0})}(new a(...u));break;case"ENDPOINT":{const{port1:t,port2:a}=new MessageChannel;d(e,a),m=function(e,t){return b.set(e,t),e}(t,[t])}break;case"RELEASE":m=void 0;break;default:return}}catch(e){m={value:e,[s]:0}}Promise.resolve(m).catch(e=>({value:e,[s]:0})).then(a=>{const[o,n]=y(a);t.postMessage(Object.assign(Object.assign({},o),{id:l}),n),"RELEASE"===c&&(t.removeEventListener("message",r),h(t),i in e&&"function"==typeof e[i]&&e[i]())}).catch(e=>{const[a,o]=y({value:new TypeError("Unserializable return value"),[s]:0});t.postMessage(Object.assign(Object.assign({},a),{id:l}),o)})}),t.start&&t.start()}function h(e){(function(e){return"MessagePort"===e.constructor.name})(e)&&e.close()}function p(e,t){const a=new Map;return e.addEventListener("message",function(e){const{data:t}=e;if(!t||!t.id)return;const o=a.get(t.id);if(o)try{o(t)}finally{a.delete(t.id)}}),v(e,a,[],t)}function u(e){if(e)throw new Error("Proxy has been released and is not useable")}function m(e){return k(e,new Map,{type:"RELEASE"}).then(()=>{h(e)})}const g=new WeakMap,_="FinalizationRegistry"in globalThis&&new FinalizationRegistry(e=>{const t=(g.get(e)||0)-1;g.set(e,t),0===t&&m(e)});function v(e,t,a=[],o=function(){}){let i=!1;const s=new Proxy(o,{get(o,r){if(u(i),r===n)return()=>{!function(e){_&&_.unregister(e)}(s),m(e),t.clear(),i=!0};if("then"===r){if(0===a.length)return{then:()=>s};const o=k(e,t,{type:"GET",path:a.map(e=>e.toString())}).then(w);return o.then.bind(o)}return v(e,t,[...a,r])},set(o,r,n){u(i);const[s,l]=y(n);return k(e,t,{type:"SET",path:[...a,r].map(e=>e.toString()),value:s},l).then(w)},apply(o,n,s){u(i);const l=a[a.length-1];if(l===r)return k(e,t,{type:"ENDPOINT"}).then(w);if("bind"===l)return v(e,t,a.slice(0,-1));const[c,d]=f(s);return k(e,t,{type:"APPLY",path:a.map(e=>e.toString()),argumentList:c},d).then(w)},construct(o,r){u(i);const[n,s]=f(r);return k(e,t,{type:"CONSTRUCT",path:a.map(e=>e.toString()),argumentList:n},s).then(w)}});return function(e,t){const a=(g.get(t)||0)+1;g.set(t,a),_&&_.register(e,t,e)}(s,e),s}function f(e){const t=e.map(y);return[t.map(e=>e[0]),(a=t.map(e=>e[1]),Array.prototype.concat.apply([],a))];var a}const b=new WeakMap;function y(e){for(const[t,a]of c)if(a.canHandle(e)){const[o,r]=a.serialize(e);return[{type:"HANDLER",name:t,value:o},r]}return[{type:"RAW",value:e},b.get(e)||[]]}function w(e){switch(e.type){case"HANDLER":return c.get(e.name).deserialize(e.value);case"RAW":return e.value}}function k(e,t,a,o){return new Promise(r=>{const n=new Array(4).fill(0).map(()=>Math.floor(Math.random()*Number.MAX_SAFE_INTEGER).toString(16)).join("-");t.set(n,r),e.start&&e.start(),e.postMessage(Object.assign({id:n},a),o)})}}};
//# sourceMappingURL=22630.31df046049b6855a.js.map