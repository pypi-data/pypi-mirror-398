/*! For license information please see 44619.1abdb92ebecdcc8d.js.LICENSE.txt */
export const __webpack_id__="44619";export const __webpack_ids__=["44619"];export const __webpack_modules__={69709:function(e,t,o){o(18111),o(22489),o(61701),o(18237);var n=o(62826),r=o(96196),a=o(44457),i=o(1420),s=o(30015),c=o.n(s),l=o(1087),h=(o(14603),o(47566),o(98721),o(2209));let d;var p=o(996);const u=e=>r.qy`${e}`,m=new p.G(1e3),g={reType:/(?<input>(\[!(?<type>caution|important|note|tip|warning)\])(?:\s|\\n)?)/i,typeToHaAlert:{caution:"error",important:"info",note:"info",tip:"success",warning:"warning"}};class _ extends r.mN{disconnectedCallback(){if(super.disconnectedCallback(),this.cache){const e=this._computeCacheKey();m.set(e,this.innerHTML)}}createRenderRoot(){return this}update(e){super.update(e),void 0!==this.content&&(this._renderPromise=this._render())}async getUpdateComplete(){return await super.getUpdateComplete(),await this._renderPromise,!0}willUpdate(e){if(!this.innerHTML&&this.cache){const e=this._computeCacheKey();m.has(e)&&((0,r.XX)(u((0,i._)(m.get(e))),this.renderRoot),this._resize())}}_computeCacheKey(){return c()({content:this.content,allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl,breaks:this.breaks})}async _render(){const e=await(async(e,t,n)=>(d||(d=(0,h.LV)(new Worker(new URL(o.p+o.u("55640"),o.b)))),d.renderMarkdown(e,t,n)))(String(this.content),{breaks:this.breaks,gfm:!0},{allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl});(0,r.XX)(u((0,i._)(e.join(""))),this.renderRoot),this._resize();const t=document.createTreeWalker(this,NodeFilter.SHOW_ELEMENT,null);for(;t.nextNode();){const e=t.currentNode;if(e instanceof HTMLAnchorElement&&e.host!==document.location.host)e.target="_blank",e.rel="noreferrer noopener";else if(e instanceof HTMLImageElement)this.lazyImages&&(e.loading="lazy"),e.addEventListener("load",this._resize);else if(e instanceof HTMLQuoteElement){const o=e.firstElementChild?.firstChild?.textContent&&g.reType.exec(e.firstElementChild.firstChild.textContent);if(o){const{type:n}=o.groups,r=document.createElement("ha-alert");r.alertType=g.typeToHaAlert[n.toLowerCase()],r.append(...Array.from(e.childNodes).map(e=>{const t=Array.from(e.childNodes);if(!this.breaks&&t.length){const e=t[0];e.nodeType===Node.TEXT_NODE&&e.textContent===o.input&&e.textContent?.includes("\n")&&(e.textContent=e.textContent.split("\n").slice(1).join("\n"))}return t}).reduce((e,t)=>e.concat(t),[]).filter(e=>e.textContent&&e.textContent!==o.input)),t.parentNode().replaceChild(r,e)}}else e instanceof HTMLElement&&["ha-alert","ha-qr-code","ha-icon","ha-svg-icon"].includes(e.localName)&&o(96175)(`./${e.localName}`)}}constructor(...e){super(...e),this.allowSvg=!1,this.allowDataUrl=!1,this.breaks=!1,this.lazyImages=!1,this.cache=!1,this._renderPromise=Promise.resolve(),this._resize=()=>(0,l.r)(this,"content-resize")}}(0,n.__decorate)([(0,a.MZ)()],_.prototype,"content",void 0),(0,n.__decorate)([(0,a.MZ)({attribute:"allow-svg",type:Boolean})],_.prototype,"allowSvg",void 0),(0,n.__decorate)([(0,a.MZ)({attribute:"allow-data-url",type:Boolean})],_.prototype,"allowDataUrl",void 0),(0,n.__decorate)([(0,a.MZ)({type:Boolean})],_.prototype,"breaks",void 0),(0,n.__decorate)([(0,a.MZ)({type:Boolean,attribute:"lazy-images"})],_.prototype,"lazyImages",void 0),(0,n.__decorate)([(0,a.MZ)({type:Boolean})],_.prototype,"cache",void 0),_=(0,n.__decorate)([(0,a.EM)("ha-markdown-element")],_)},3587:function(e,t,o){var n=o(62826),r=o(96196),a=o(44457);o(69709);class i extends r.WF{async getUpdateComplete(){const e=await super.getUpdateComplete();return await(this._markdownElement?.updateComplete),e}render(){return this.content?r.qy`<ha-markdown-element .content="${this.content}" .allowSvg="${this.allowSvg}" .allowDataUrl="${this.allowDataUrl}" .breaks="${this.breaks}" .lazyImages="${this.lazyImages}" .cache="${this.cache}"></ha-markdown-element>`:r.s6}constructor(...e){super(...e),this.allowSvg=!1,this.allowDataUrl=!1,this.breaks=!1,this.lazyImages=!1,this.cache=!1}}i.styles=r.AH`
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
  `,(0,n.__decorate)([(0,a.MZ)()],i.prototype,"content",void 0),(0,n.__decorate)([(0,a.MZ)({attribute:"allow-svg",type:Boolean})],i.prototype,"allowSvg",void 0),(0,n.__decorate)([(0,a.MZ)({attribute:"allow-data-url",type:Boolean})],i.prototype,"allowDataUrl",void 0),(0,n.__decorate)([(0,a.MZ)({type:Boolean})],i.prototype,"breaks",void 0),(0,n.__decorate)([(0,a.MZ)({type:Boolean,attribute:"lazy-images"})],i.prototype,"lazyImages",void 0),(0,n.__decorate)([(0,a.MZ)({type:Boolean})],i.prototype,"cache",void 0),(0,n.__decorate)([(0,a.P)("ha-markdown-element")],i.prototype,"_markdownElement",void 0),i=(0,n.__decorate)([(0,a.EM)("ha-markdown")],i)},84334:function(e,t,o){o.d(t,{H:()=>r,R:()=>n});const n=(e,t,o)=>e.subscribeMessage(e=>t(e),{type:"render_template",...o}),r=(e,t,o,n,r)=>e.connection.subscribeMessage(r,{type:"template/start_preview",flow_id:t,flow_type:o,user_input:n})},67334:function(e,t,o){o.r(t),o.d(t,{HuiMarkdownCard:()=>u});var n=o(62826),r=o(96196),a=o(44457),i=o(94333),s=o(30015),c=o.n(s),l=o(42372),h=o(1087),d=(o(38962),o(76776),o(3587),o(84334));const p=new(o(996).G)(1e3);class u extends r.WF{static async getConfigElement(){return await o.e("90742").then(o.bind(o,4757)),document.createElement("hui-markdown-card-editor")}static getStubConfig(){return{type:"markdown",content:"The **Markdown** card allows you to write any text. You can style it **bold**, *italicized*, ~strikethrough~ etc. You can do images, links, and more.\n\nFor more information see the [Markdown Cheatsheet](https://commonmark.org/help)."}}getCardSize(){return void 0===this._config?3:void 0===this._config.card_size?Math.round(this._config.content.split("\n").length/2)+(this._config.title?1:0):this._config.card_size}setConfig(e){if(!e.content)throw new Error("Content required");this._config?.content!==e.content&&this._tryDisconnect(),this._config=e}connectedCallback(){super.connectedCallback(),this._tryConnect()}_computeCacheKey(){return c()(this._config)}disconnectedCallback(){if(super.disconnectedCallback(),this._tryDisconnect(),this._config&&this._templateResult){const e=this._computeCacheKey();p.set(e,this._templateResult)}}willUpdate(e){if(super.willUpdate(e),this._config&&!this._templateResult){const e=this._computeCacheKey();p.has(e)&&(this._templateResult=p.get(e))}}render(){return this._config?r.qy` ${this._error?r.qy` <ha-alert .alertType="${this._errorLevel?.toLowerCase()||"error"}"> ${this._error} </ha-alert> `:r.s6} <ha-card .header="${this._config.text_only?void 0:this._config.title}" class="${(0,i.H)({"with-header":!!this._config.title,"text-only":this._config.text_only??!1})}"> <ha-markdown cache breaks .content="${this._templateResult?.result}"></ha-markdown> </ha-card> `:r.s6}updated(e){if(super.updated(e),!this._config||!this.hass)return;e.has("_config")&&this._tryConnect();const t=!!this._templateResult&&!1===this._config.show_empty&&0===this._templateResult.result.length;t!==this.hidden&&(this.style.display=t?"none":"",this.toggleAttribute("hidden",t),(0,h.r)(this,"card-visibility-changed",{value:!t}));const o=e.get("hass"),n=e.get("_config");o&&n&&o.themes===this.hass.themes&&n.theme===this._config.theme||(0,l.Q)(this,this.hass.themes,this._config.theme)}async _tryConnect(){if(void 0===this._unsubRenderTemplate&&this.hass&&this._config){this._error=void 0,this._errorLevel=void 0;try{this._unsubRenderTemplate=(0,d.R)(this.hass.connection,e=>{"error"in e?"ERROR"!==e.level&&"ERROR"===this._errorLevel||(this._error=e.error,this._errorLevel=e.level):this._templateResult=e},{template:this._config.content,entity_ids:this._config.entity_id,variables:{config:this._config,user:this.hass.user.name},strict:!0,report_errors:this.preview}),await this._unsubRenderTemplate}catch(e){this.preview&&(this._error=e.message,this._errorLevel=void 0),this._templateResult={result:this._config.content,listeners:{all:!1,domains:[],entities:[],time:!1}},this._unsubRenderTemplate=void 0}}}async _tryDisconnect(){this._unsubRenderTemplate&&(this._unsubRenderTemplate.then(e=>e()).catch(),this._unsubRenderTemplate=void 0,this._error=void 0,this._errorLevel=void 0)}constructor(...e){super(...e),this.preview=!1}}u.styles=r.AH`ha-card{height:100%;overflow-y:auto}ha-alert{margin-bottom:8px}ha-markdown{padding:16px;word-wrap:break-word;text-align:var(--card-text-align,inherit)}.with-header ha-markdown{padding:0 16px 16px}.text-only{background:0 0;box-shadow:none;border:none}.text-only ha-markdown{padding:2px 4px}`,(0,n.__decorate)([(0,a.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,n.__decorate)([(0,a.MZ)({type:Boolean})],u.prototype,"preview",void 0),(0,n.__decorate)([(0,a.wk)()],u.prototype,"_config",void 0),(0,n.__decorate)([(0,a.wk)()],u.prototype,"_error",void 0),(0,n.__decorate)([(0,a.wk)()],u.prototype,"_errorLevel",void 0),(0,n.__decorate)([(0,a.wk)()],u.prototype,"_templateResult",void 0),u=(0,n.__decorate)([(0,a.EM)("hui-markdown-card")],u)},996:function(e,t,o){o.d(t,{G:()=>n});class n{get(e){return this._cache.get(e)}set(e,t){this._cache.set(e,t),this._expiration&&window.setTimeout(()=>this._cache.delete(e),this._expiration)}has(e){return this._cache.has(e)}constructor(e){this._cache=new Map,this._expiration=e}}},96175:function(e,t,o){var n={"./ha-icon-prev":["89133","61982"],"./ha-icon-button-toolbar":["9882","26431","76775"],"./ha-alert":["38962","19695"],"./ha-icon-button-toggle":["62501","77254"],"./ha-svg-icon.ts":["67094"],"./ha-alert.ts":["38962","19695"],"./ha-icon":["88945","51146"],"./ha-icon-next.ts":["43661","63902"],"./ha-qr-code.ts":["60543","51343","62740"],"./ha-icon-overflow-menu.ts":["75248","46095","26431","22016","56297"],"./ha-icon-button-toggle.ts":["62501","77254"],"./ha-icon-button-group":["39826","13647"],"./ha-svg-icon":["67094"],"./ha-icon-button-prev":["45100","99197"],"./ha-icon-button.ts":["26300"],"./ha-icon-overflow-menu":["75248","46095","26431","22016","56297"],"./ha-icon-button-arrow-next":["99028","54101"],"./ha-icon-button-prev.ts":["45100","99197"],"./ha-icon-picker":["64138","44533","7199","46095","48654","72991"],"./ha-icon-button-toolbar.ts":["9882","26431","76775"],"./ha-icon-button-arrow-prev.ts":["90248","17041"],"./ha-icon-button-next":["25440","81049"],"./ha-icon-next":["43661","63902"],"./ha-icon-picker.ts":["64138","44533","7199","46095","48654","72991"],"./ha-icon-prev.ts":["89133","61982"],"./ha-icon-button-arrow-prev":["90248","17041"],"./ha-icon-button-next.ts":["25440","81049"],"./ha-icon.ts":["88945","51146"],"./ha-qr-code":["60543","51343","62740"],"./ha-icon-button":["26300"],"./ha-icon-button-group.ts":["39826","13647"],"./ha-icon-button-arrow-next.ts":["99028","54101"]};function r(e){if(!o.o(n,e))return Promise.resolve().then(function(){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t});var t=n[e],r=t[0];return Promise.all(t.slice(1).map(o.e)).then(function(){return o(r)})}r.keys=()=>Object.keys(n),r.id=96175,e.exports=r},2209:function(e,t,o){o.d(t,{LV:()=>p});o(18111),o(61701),o(18237);const n=Symbol("Comlink.proxy"),r=Symbol("Comlink.endpoint"),a=Symbol("Comlink.releaseProxy"),i=Symbol("Comlink.finalizer"),s=Symbol("Comlink.thrown"),c=e=>"object"==typeof e&&null!==e||"function"==typeof e,l=new Map([["proxy",{canHandle:e=>c(e)&&e[n],serialize(e){const{port1:t,port2:o}=new MessageChannel;return h(e,t),[o,[o]]},deserialize:e=>(e.start(),p(e))}],["throw",{canHandle:e=>c(e)&&s in e,serialize({value:e}){let t;return t=e instanceof Error?{isError:!0,value:{message:e.message,name:e.name,stack:e.stack}}:{isError:!1,value:e},[t,[]]},deserialize(e){if(e.isError)throw Object.assign(new Error(e.value.message),e.value);throw e.value}}]]);function h(e,t=globalThis,o=["*"]){t.addEventListener("message",function r(a){if(!a||!a.data)return;if(!function(e,t){for(const o of e){if(t===o||"*"===o)return!0;if(o instanceof RegExp&&o.test(t))return!0}return!1}(o,a.origin))return void console.warn(`Invalid origin '${a.origin}' for comlink proxy`);const{id:c,type:l,path:p}=Object.assign({path:[]},a.data),u=(a.data.argumentList||[]).map(y);let m;try{const t=p.slice(0,-1).reduce((e,t)=>e[t],e),o=p.reduce((e,t)=>e[t],e);switch(l){case"GET":m=o;break;case"SET":t[p.slice(-1)[0]]=y(a.data.value),m=!0;break;case"APPLY":m=o.apply(t,u);break;case"CONSTRUCT":m=function(e){return Object.assign(e,{[n]:!0})}(new o(...u));break;case"ENDPOINT":{const{port1:t,port2:o}=new MessageChannel;h(e,o),m=function(e,t){return b.set(e,t),e}(t,[t])}break;case"RELEASE":m=void 0;break;default:return}}catch(e){m={value:e,[s]:0}}Promise.resolve(m).catch(e=>({value:e,[s]:0})).then(o=>{const[n,a]=f(o);t.postMessage(Object.assign(Object.assign({},n),{id:c}),a),"RELEASE"===l&&(t.removeEventListener("message",r),d(t),i in e&&"function"==typeof e[i]&&e[i]())}).catch(e=>{const[o,n]=f({value:new TypeError("Unserializable return value"),[s]:0});t.postMessage(Object.assign(Object.assign({},o),{id:c}),n)})}),t.start&&t.start()}function d(e){(function(e){return"MessagePort"===e.constructor.name})(e)&&e.close()}function p(e,t){const o=new Map;return e.addEventListener("message",function(e){const{data:t}=e;if(!t||!t.id)return;const n=o.get(t.id);if(n)try{n(t)}finally{o.delete(t.id)}}),w(e,o,[],t)}function u(e){if(e)throw new Error("Proxy has been released and is not useable")}function m(e){return k(e,new Map,{type:"RELEASE"}).then(()=>{d(e)})}const g=new WeakMap,_="FinalizationRegistry"in globalThis&&new FinalizationRegistry(e=>{const t=(g.get(e)||0)-1;g.set(e,t),0===t&&m(e)});function w(e,t,o=[],n=function(){}){let i=!1;const s=new Proxy(n,{get(n,r){if(u(i),r===a)return()=>{!function(e){_&&_.unregister(e)}(s),m(e),t.clear(),i=!0};if("then"===r){if(0===o.length)return{then:()=>s};const n=k(e,t,{type:"GET",path:o.map(e=>e.toString())}).then(y);return n.then.bind(n)}return w(e,t,[...o,r])},set(n,r,a){u(i);const[s,c]=f(a);return k(e,t,{type:"SET",path:[...o,r].map(e=>e.toString()),value:s},c).then(y)},apply(n,a,s){u(i);const c=o[o.length-1];if(c===r)return k(e,t,{type:"ENDPOINT"}).then(y);if("bind"===c)return w(e,t,o.slice(0,-1));const[l,h]=v(s);return k(e,t,{type:"APPLY",path:o.map(e=>e.toString()),argumentList:l},h).then(y)},construct(n,r){u(i);const[a,s]=v(r);return k(e,t,{type:"CONSTRUCT",path:o.map(e=>e.toString()),argumentList:a},s).then(y)}});return function(e,t){const o=(g.get(t)||0)+1;g.set(t,o),_&&_.register(e,t,e)}(s,e),s}function v(e){const t=e.map(f);return[t.map(e=>e[0]),(o=t.map(e=>e[1]),Array.prototype.concat.apply([],o))];var o}const b=new WeakMap;function f(e){for(const[t,o]of l)if(o.canHandle(e)){const[n,r]=o.serialize(e);return[{type:"HANDLER",name:t,value:n},r]}return[{type:"RAW",value:e},b.get(e)||[]]}function y(e){switch(e.type){case"HANDLER":return l.get(e.name).deserialize(e.value);case"RAW":return e.value}}function k(e,t,o,n){return new Promise(r=>{const a=new Array(4).fill(0).map(()=>Math.floor(Math.random()*Number.MAX_SAFE_INTEGER).toString(16)).join("-");t.set(a,r),e.start&&e.start(),e.postMessage(Object.assign({id:a},o),n)})}}};
//# sourceMappingURL=44619.1abdb92ebecdcc8d.js.map