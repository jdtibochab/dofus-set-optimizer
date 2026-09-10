import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from chromosome import Chromosome


def construct_report_str(chromosome):
    report_lines = []
    report_lines.append(f"\tFitness: {chromosome.fitness}")
    report_lines.append(f"\tWeapon damage: {chromosome.get_final_damage(type='weapon')}")
    wpn = chromosome.weapon['name'][chromosome.optimizer.config.get('language', 'en')]
    report_lines.append(f"\t\tWeapon: {wpn}")
    report_lines.append(f"\t\tAP Cost: {chromosome.weapon['apCost']}")
    report_lines.append(f"\t\tCasts per turn: {chromosome.weapon['maxCastPerTurn']}")
    dmg = chromosome.get_final_damage(type="elements")
    report_lines.append(f"\tSpell damage:{dmg}")
    # file.write("\tIs the solution viable?", solution.viable)
    # file.write("\tWas the solution penalized?", solution.penalized)

    report_lines.append("\tPreferences:")
    df = chromosome.totals_summary()
    for bound, preference in chromosome.preferences.items():
        _report_preferences = set(preference.keys()).union({
            29, # Crit
            24, # Initiative
            26, # Placaje
            59, # Huida
            32, # Potencia
        })
        _report_preferences = [int(i) for i in sorted(list(_report_preferences)) if i in df.index]
        for i, row in df.loc[_report_preferences].sort_values("description").iterrows():
            report_lines.append(f"\t\t{row['description']} : {row['value']}")
    report_lines.append("\tCharacteristics:")
    for element in chromosome.elements:
        element = int(element)
        report_lines.append(f"\t\t{df.loc[element]['description']}: {df.loc[element]['value']}")

    report_lines.append("\tItems:")
    report_lines.append("\t\tType\tDescription\tLevel\tID")
    sorted_summary = chromosome.set_summary().sort_values("type")
    for item,row in sorted_summary.iterrows():
        # Prettify the output
        report_lines.append(f"\t\t{row['type']}\t{row['description']}\t{row['level']}\t{item}")

    chromosome_strings = [f"\t\t\t{gene}, # {row['description']}\n" for gene,row in sorted_summary.iterrows()]
    phrase = "".join(chromosome_strings)
    report_lines.append(f"\tChromosome: [\n{phrase}\t\t\t]")
    report_lines.append("")
    return "\n".join(report_lines)

class Analyzer:
    def __init__(self, opt, solutions):
        self.optimizer = opt
        self.solutions = solutions
        self.candidates = []
        self.df_totals = pd.DataFrame()
        self.df_totals_normalized = pd.DataFrame()

    def get_candidate_solutions(self):
        candidates = []
        # If we use this best fitness, it might bias the results towards one island
        # If we dont, we include solutions that are way worse and skew the PCA
        best_fitness = sorted(self.solutions, key=lambda x: x.fitness, reverse=True)[0].fitness
        for sol in self.solutions:
            # Get list of solutions
            lst_solutions = sol.best_solutions
            lst_fitness = sol.best_solutions_fitness
            # Base candidates off the best fitness of every island to get diversity
            # best_fitness = max(lst_fitness)
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
        # self.candidates = candidates
        self.candidates = sorted(candidates,key=lambda x: x.fitness, reverse=True)


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
        if not hasattr(self, 'principal_components'):
            return
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

        top_n = 10  # or 15, or whatever number you want
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
        if len(self.candidates) == 0:
            return
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
        path =self.optimizer.config["path"]
        filename = f"{path}/report.txt"
        with open(filename,"w") as file:
            for idx, solution in enumerate(lst_solutions):
                report = construct_report_str(solution)
                file.write(f"Solution {idx}:\n")
                file.write(report + "\n")

    def report_extended_results(self):
        self.report_results(self.candidates)

    def report_best_results(self):
        self.report_results(self.solutions)