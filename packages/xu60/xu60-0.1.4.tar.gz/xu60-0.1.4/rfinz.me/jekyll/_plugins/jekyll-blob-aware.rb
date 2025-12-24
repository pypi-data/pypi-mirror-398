module Jekyll
  class BlobContextGenerator < Generator
    def generate(site)
      for p in  site.posts.docs.each
        org_path = p.relative_path.gsub(/\.html$/, '.org')
        commit = %x[git rev-list HEAD -1 -- $(git rev-parse --show-toplevel)/org/#{org_path}]
        p.data['commit'] = commit
        p.data['org'] = File.join('org', org_path)
      end
    end
  end
end
