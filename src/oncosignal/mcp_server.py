"""Serveur MCP SDK v1, lecture seule, transport stdio local."""
from .config import Settings
from .pipeline import ResearchWorkspace
from .quality import report
from .alignment import links

def make_server(service=None):
    from mcp.server.fastmcp import FastMCP
    workspace=service or ResearchWorkspace(Settings.from_env())
    mcp=FastMCP('OncoSignal')

    @mcp.tool()
    def search_evidence(query:str,limit:int=5)->list:
        """Cherche des sources locales avec extraits, URL et empreinte. Pas de décision clinique."""
        if len(query)>1000 or not 1<=limit<=20:raise ValueError('Requête <=1000 caractères, limite 1..20')
        return workspace.search.query(query,limit=limit)

    @mcp.tool()
    def get_record(record_id:str)->dict:
        """Lit une notice et sa provenance ; les notices rejetées ne sont pas exposées par MCP."""
        r=workspace.store.get(record_id)
        if not r or r.review=='rejected':return {'error':'Notice absente ou rejetée'}
        return {**r.model_dump(),'content_hash':r.content_hash}

    @mcp.tool()
    def quality_report()->dict:
        """Retourne les contrôles de qualité et leurs limites."""
        return report(workspace.store.records())

    @mcp.tool()
    def trial_publication_links()->list:
        """Liens par NCT explicite ; validation humaine requise."""
        return links(workspace.store.records())

    return mcp

def main():make_server().run(transport='stdio')

if __name__=='__main__':main()
