import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import pandas as pd
from chromosome import Chromosome


class Analyzer(object):
    def __init__(self, opt, solutions):
        self.optimizer = opt
        self.solutions = solutions
        self.candidates = []
        self.df_totals = pd.DataFrame()
        self.df_totals_normalized = pd.DataFrame()

    def get_candidate_solutions(self):
        candidates = []
        best_fitness = sorted(self.solutions, key=lambda x: x.fitness, reverse=True)[0].fitness
        for sol in self.solutions:
            # Get list of solutions
            lst_solutions = sol.best_solutions
            lst_fitness = sol.best_solutions_fitness
            df = pd.DataFrame(lst_solutions)

            # Remove duplicates
            # 'keep' can be 'first', 'last', or False (mark all duplicates as True)
            unique_mask = ~df.duplicated(keep='first')
            unique_indices = df.index[unique_mask].to_list()
            unique_fitness = [lst_fitness[i] for i in unique_indices]

            # Filter candidates
            sorted_unique_indices = pd.Series({idx:f for idx, f in zip(unique_indices, unique_fitness)}).sort_values(ascending=False)
            candidate_indices = sorted_unique_indices.index[sorted_unique_indices.values >= 0.9 * best_fitness]
            for i in candidate_indices:
                chr = Chromosome(lst_solutions[i],
                                  self.optimizer)
                if chr.penalized:
                    continue
                candidates.append(chr)
        print(f"Number of candidate solutions: {len(candidates)}")
        self.candidates = candidates

    def get_valid_data(self):
        exclude = [179,225,72]
        dct_totals = {}
        lst_fitness = []
        for idx,candidate in enumerate(self.candidates):
            dct_totals[idx] = candidate.totals
            lst_fitness.append(candidate.fitness)
        df_totals = pd.DataFrame.from_dict(dct_totals, orient='index').fillna(0.)
        df_totals = df_totals[[i for i in df_totals.columns if i not in exclude]]
        df_totals.columns = df_totals.columns.map(lambda x: self.optimizer.effect_descriptions.get(x, {}).get('es', x))
        self.df_totals = df_totals
        self.lst_fitness = lst_fitness


    def normalize_totals(self):
        # Normalize totals
        df_totals_normalized = (self.df_totals - self.df_totals.mean()) / self.df_totals.std()
        df_totals_normalized = df_totals_normalized.dropna(axis=1)
        self.df_totals_normalized = df_totals_normalized

    def run_pca(self):
        # Run PCA
        n_components = 2
        self.pca = PCA(n_components=n_components)
        self.principal_components = self.pca.fit_transform(self.df_totals_normalized.values)

    def plot_pca(self):
        # Visualize
        plt.figure(figsize=(8,6))
        # Mask data points with fitness value
        # plt.scatter(principal_components[:,0], principal_components[:,1], alpha=0.7)
        plt.scatter(self.principal_components[:,0], self.principal_components[:,1], c=self.lst_fitness, cmap='viridis', alpha=0.7)
        plt.colorbar(label='Fitness Value')
        # Plot the index of each point
        for i in range(len(self.principal_components)):
            plt.annotate(i, (self.principal_components[i, 0], self.principal_components[i, 1]), fontsize=8)

        # Calculate variance explained by each PC
        explained_variance = self.pca.explained_variance_ratio_
        plt.xlabel(f'PC 1 ({explained_variance[0]:.2%})')
        plt.ylabel(f'PC 2 ({explained_variance[1]:.2%})')
        plt.title('PCA of Final Solutions')

        # Add quivers
        import numpy as np
        # Loadings for PC1 and PC2 for each feature
        loadings = self.pca.components_[:2, :]  # shape (2, n_features)
        loading_magnitudes = np.linalg.norm(loadings, axis=0)  # shape (n_features,)

        top_n = 20  # or 15, or whatever number you want
        top_indices = np.argsort(loading_magnitudes)[-top_n:]  # indices of top N features

        stat_names = self.df_totals_normalized.columns.tolist()  # Replace with your stat names if you have them
        scaling = 10  # Adjust as needed for visibility

        for i in top_indices:
            x = self.pca.components_[0, i]
            y = self.pca.components_[1, i]
            plt.arrow(0, 0, x*scaling, y*scaling, color='r', alpha=0.7, head_width=0.05)
            plt.text(x*scaling*1.15, y*scaling*1.15+np.random.normal()*0.1, stat_names[i], color='r', ha='center', va='center', fontsize=9)

        # # Inspect contributions
        # gene_names = df_totals_normalized.columns.tolist()
        # pc_df = pd.DataFrame(pca.components_, columns=gene_names, index=[f"PC{i+1}" for i in range(n_components)])
        # print("Gene contributions to each PC:")
        # # pc_df.T.sort_values(by='PC1', ascending=True)
        # pc_df.T.sort_values(by='PC1', ascending=True)["PC1"].plot.barh(figsize=(5,10))

    def run_analysis(self):
        self.get_candidate_solutions()
        self.get_valid_data()
        self.normalize_totals()
        self.run_pca()
        # self.plot_pca()

    def report_generations(self):
        depth = int(np.ceil(len(self.solutions)/4))
        fig,ax = plt.subplots(depth,4,figsize=(10,depth*2))
        ax = ax.flatten()
        for axi,solution in zip(ax,self.solutions):
            axi.plot(solution.best_solutions_fitness)
            axi.set_xlabel('Generation')
            axi.set_ylabel('Best Fitness')
        fig.tight_layout()

    def report_results(self, lst_solutions):
        from utils import elements
        for idx, solution in enumerate(sorted(lst_solutions,
                                               key=lambda x: x.fitness, reverse=True)):
            if solution.penalized:
                continue
            print(f"Solution {idx}:")
            print("\tFitness:", solution.get_fitness())
            print("\tWeapon damage:", solution.get_final_damage(type="weapon"))
            print("\tSpell damage:", solution.get_final_damage(type="elements"))
            # print("\tIs the solution viable?", solution.viable)
            # print("\tWas the solution penalized?", solution.penalized)

            print("\tPreferences:")
            df = solution.totals_summary()
            for bound, preference in solution.preferences.items():
                for element, details in preference.items():
                    row = df.loc[element]
                    print(f"\t\t{row['description']} : {row['value']}")
            print("\tCharacteristics:")
            for element in elements:
                print(f"\t\t{df.loc[element]['description']}: {df.loc[element]['value']}")

            print("\tItems:")
            print("\t\tType\tDescription\tLevel")
            for item,row in solution.set_summary().sort_values("type").iterrows():
                # Prettify the output
                print(f"\t\t{row['type']}\t{row['description']}\t{row['level']}")

    def report_extended_results(self):
        self.report_results(self.candidates)

    def report_best_results(self):
        self.report_results(self.solutions)